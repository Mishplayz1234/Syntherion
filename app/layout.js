import './globals.css'

export const metadata = {
  title: 'Syntherion AI - Intelligent Chat Assistant',
  description: 'A modern AI chatbot powered by Mistral 7B with user authentication and chat history',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}