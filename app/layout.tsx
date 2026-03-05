import { Inter, IBM_Plex_Mono } from 'next/font/google'
import type { Metadata } from 'next'
import './globals.css'

const inter = Inter({
    subsets: ['latin'],
    variable: '--font-inter',
    weight: ['300', '400', '500', '600', '700'],
    display: 'swap',
})

const ibmPlexMono = IBM_Plex_Mono({
    subsets: ['latin'],
    variable: '--font-ibm-plex-mono',
    weight: ['400', '500', '600'],
    display: 'swap',
})

export const metadata: Metadata = {
    title: 'FloatChat Ultimate - AI-Powered Ocean Data Platform',
    description: 'The most advanced AI-powered ocean intelligence platform. Make ocean data as accessible as a Google search.',
    keywords: ['ocean data', 'ARGO floats', 'AI', 'oceanography', 'data visualization'],
}

import Sidebar from '@/components/Sidebar'

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode
}>) {
    return (
        <html lang="en" className="dark">
            <body className={`${inter.variable} ${ibmPlexMono.variable} font-sans antialiased bg-black text-white`} style={{ display: 'flex', flexDirection: 'row', height: '100vh', overflow: 'hidden' }}>
                <Sidebar />
                <main id="main-scroll" style={{ flex: 1, position: 'relative', overflowY: 'auto', overflowX: 'hidden', height: '100vh' }}>
                    {children}
                </main>
            </body>
        </html>
    )
}
