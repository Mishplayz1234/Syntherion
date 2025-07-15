import { NextResponse } from 'next/server'
import { MongoClient } from 'mongodb'
import { v4 as uuidv4 } from 'uuid'
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import OpenAI from 'openai'

const client = new MongoClient(process.env.MONGO_URL)
const dbName = process.env.DB_NAME || 'syntherion_ai'

// Create Supabase Server Client
function createSupabaseServer() {
  const cookieStore = cookies()
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {
            // Handle cookie setting errors
          }
        },
      },
    }
  )
}

// Create OpenAI client configured for OpenRouter
const openai = new OpenAI({
  apiKey: process.env.OPENROUTER_API_KEY,
  baseURL: 'https://openrouter.ai/api/v1',
})

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
}

function handleCORS(response) {
  Object.entries(corsHeaders).forEach(([key, value]) => {
    response.headers.set(key, value)
  })
  return response
}

// Connect to MongoDB
async function connectToMongoDB() {
  try {
    await client.connect()
    return client.db(dbName)
  } catch (error) {
    console.error('MongoDB connection error:', error)
    throw error
  }
}

// Authentication middleware
async function authenticateUser() {
  // Check for test user cookie/header first
  const testUserCookie = cookies().get('test-user')
  if (testUserCookie && testUserCookie.value === 'test-user-123') {
    return {
      id: 'test-user-123',
      email: '123@test.com',
      email_confirmed_at: new Date().toISOString(),
      user_metadata: {},
      app_metadata: {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  }
  
  const supabase = createSupabaseServer()
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  
  if (authError || !user) {
    return null
  }
  
  return user
}

export async function GET(request) {
  const { pathname } = new URL(request.url)
  const path = pathname.replace('/api/', '') || ''

  try {
    if (path === '') {
      return handleCORS(NextResponse.json({ message: 'Syntherion AI API is running!' }))
    }

    if (path === 'health') {
      return handleCORS(NextResponse.json({ status: 'healthy', timestamp: new Date().toISOString() }))
    }

    // Auth endpoints
    if (path === 'auth/user') {
      const user = await authenticateUser()
      if (!user) {
        return handleCORS(NextResponse.json({ error: 'Unauthorized' }, { status: 401 }))
      }
      return handleCORS(NextResponse.json({ user }))
    }

    // Get chat history
    if (path === 'chats') {
      const user = await authenticateUser()
      if (!user) {
        return handleCORS(NextResponse.json({ error: 'Unauthorized' }, { status: 401 }))
      }

      const db = await connectToMongoDB()
      const chats = await db.collection('chats')
        .find({ userId: user.id })
        .sort({ createdAt: -1 })
        .toArray()

      return handleCORS(NextResponse.json({ chats }))
    }

    return handleCORS(NextResponse.json({ error: 'Not found' }, { status: 404 }))
  } catch (error) {
    console.error('API Error:', error)
    return handleCORS(NextResponse.json({ error: 'Internal server error' }, { status: 500 }))
  }
}

export async function POST(request) {
  const { pathname } = new URL(request.url)
  const path = pathname.replace('/api/', '') || ''

  try {
    const body = await request.json()

    // Authentication endpoints
    if (path === 'auth/signup') {
      const { email, password } = body
      const supabase = createSupabaseServer()
      
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
      })

      if (error) {
        return handleCORS(NextResponse.json({ error: error.message }, { status: 400 }))
      }

      return handleCORS(NextResponse.json({ message: 'User created successfully', user: data.user }))
    }

    if (path === 'auth/signin') {
      const { email, password } = body
      
      // Bypass authentication for test credentials
      if (email === '123@test.com' && password === '123@test.com') {
        // Create a mock user session for testing
        const mockUser = {
          id: 'test-user-123',
          email: '123@test.com',
          email_confirmed_at: new Date().toISOString(),
          user_metadata: {},
          app_metadata: {},
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }
        
        // Set test user cookie
        const response = NextResponse.json({ 
          message: 'Signed in successfully (test mode)', 
          user: mockUser 
        })
        
        response.cookies.set('test-user', 'test-user-123', {
          httpOnly: true,
          secure: true,
          sameSite: 'strict',
          maxAge: 60 * 60 * 24 * 7 // 7 days
        })
        
        return handleCORS(response)
      }
      
      const supabase = createSupabaseServer()
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (error) {
        return handleCORS(NextResponse.json({ error: error.message }, { status: 400 }))
      }

      return handleCORS(NextResponse.json({ message: 'Signed in successfully', user: data.user }))
    }

    if (path === 'auth/signout') {
      const supabase = createSupabaseServer()
      
      // Check if this is a test user
      const testUserCookie = cookies().get('test-user')
      if (testUserCookie && testUserCookie.value === 'test-user-123') {
        const response = NextResponse.json({ message: 'Signed out successfully (test mode)' })
        response.cookies.delete('test-user')
        return handleCORS(response)
      }
      
      const { error } = await supabase.auth.signOut()

      if (error) {
        return handleCORS(NextResponse.json({ error: error.message }, { status: 400 }))
      }

      return handleCORS(NextResponse.json({ message: 'Signed out successfully' }))
    }

    // Chat endpoint
    if (path === 'chat') {
      const user = await authenticateUser()
      if (!user) {
        return handleCORS(NextResponse.json({ error: 'Unauthorized' }, { status: 401 }))
      }

      const { messages, sessionId } = body

      if (!messages || !Array.isArray(messages)) {
        return handleCORS(NextResponse.json({ error: 'Messages array is required' }, { status: 400 }))
      }

      try {
        // Get AI response from OpenRouter
        const response = await openai.chat.completions.create({
          model: 'mistralai/mistral-7b-instruct',
          messages: messages,
          max_tokens: 1000,
          temperature: 0.7,
        })

        const aiMessage = response.choices[0].message.content

        // Save chat to MongoDB
        const db = await connectToMongoDB()
        const chat = {
          id: uuidv4(),
          userId: user.id,
          userEmail: user.email,
          sessionId: sessionId || uuidv4(),
          messages: [...messages, { role: 'assistant', content: aiMessage }],
          createdAt: new Date(),
          updatedAt: new Date()
        }

        await db.collection('chats').insertOne(chat)

        return handleCORS(NextResponse.json({ 
          message: aiMessage,
          sessionId: chat.sessionId,
          chatId: chat.id
        }))
      } catch (error) {
        console.error('OpenRouter API Error:', error)
        return handleCORS(NextResponse.json({ error: 'Failed to get AI response' }, { status: 500 }))
      }
    }

    return handleCORS(NextResponse.json({ error: 'Not found' }, { status: 404 }))
  } catch (error) {
    console.error('API Error:', error)
    return handleCORS(NextResponse.json({ error: 'Internal server error' }, { status: 500 }))
  }
}

export async function OPTIONS(request) {
  return handleCORS(new Response(null, { status: 200 }))
}