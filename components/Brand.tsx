/**
 * Brand.tsx – FloatChat custom minimalist logo marks
 * Used across nav pills, chat header, and welcome state.
 */

/** FloatChat wordmark – float buoy icon + text */
export function FloatChatLogo({ size = 17 }: { size?: number }) {
    return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
            {/* Float buoy mark: filled circle above a sine wave */}
            <svg width={size} height={size} viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                {/* Buoy float */}
                <circle cx="10" cy="6.5" r="3.8" fill="#0071e3" />
                {/* Ocean wave */}
                <path
                    d="M1.5 14.5 C3.5 12.5 5.5 12.5 7.5 14.5 C9.5 16.5 11.5 16.5 13.5 14.5 C15.5 12.5 17.5 12.5 18.5 13.5"
                    stroke="#0071e3"
                    strokeWidth="1.9"
                    strokeLinecap="round"
                    fill="none"
                />
            </svg>
            <span style={{ fontSize: 14, fontWeight: 800, letterSpacing: '-0.03em', color: '#1d1d1f', fontFamily: "'Inter', -apple-system, sans-serif" }}>
                FloatChat
            </span>
        </span>
    )
}

/**
 * OceanAI app icon badge – rounded square with dual-wave mark.
 * Used in the chat page header as the "AI" identity avatar.
 */
export function OceanAIBadge({ size = 34 }: { size?: number }) {
    const r = size * 0.32   // border radius
    return (
        <svg width={size} height={size} viewBox="0 0 34 34" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Rounded square bg */}
            <rect width="34" height="34" rx={r} fill="#0071e3" />
            {/* Primary wave */}
            <path
                d="M7 20 C9.5 17.5 12 17.5 14.5 20 C17 22.5 19.5 22.5 22 20 C24.5 17.5 27 17.5 27 17.5"
                stroke="white"
                strokeWidth="2.1"
                strokeLinecap="round"
                fill="none"
            />
            {/* Secondary wave (dimmer — depth) */}
            <path
                d="M7 14 C9.5 11.5 12 11.5 14.5 14 C17 16.5 19.5 16.5 22 14 C24.5 11.5 27 11.5 27 11.5"
                stroke="rgba(255,255,255,0.45)"
                strokeWidth="1.6"
                strokeLinecap="round"
                fill="none"
            />
        </svg>
    )
}

/**
 * FloatMarkIcon – standalone icon only (no text), used in welcome state hero.
 */
export function FloatMarkIcon({ size = 28, color = '#fff' }: { size?: number; color?: string }) {
    return (
        <svg width={size} height={size} viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Buoy float */}
            <circle cx="14" cy="9" r="5.2" fill={color} />
            {/* Three-line wave */}
            <path
                d="M3 20 C5.5 17.5 8 17.5 10.5 20 C13 22.5 15.5 22.5 18 20 C20.5 17.5 23 17.5 25 19"
                stroke={color}
                strokeWidth="2.4"
                strokeLinecap="round"
                fill="none"
            />
        </svg>
    )
}
