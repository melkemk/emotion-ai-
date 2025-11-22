import { useState, useEffect } from 'react'

interface TypingTextProps {
    text: string
    speed?: number
    onComplete?: () => void
}

export function TypingText({ text, speed = 30, onComplete }: TypingTextProps) {
    const [displayedText, setDisplayedText] = useState('')
    const [currentIndex, setCurrentIndex] = useState(0)

    useEffect(() => {
        if (currentIndex < text.length) {
            const timeout = setTimeout(() => {
                setDisplayedText(prev => prev + text[currentIndex])
                setCurrentIndex(prev => prev + 1)
            }, speed)

            return () => clearTimeout(timeout)
        } else if (onComplete && currentIndex === text.length) {
            onComplete()
        }
    }, [currentIndex, text, speed, onComplete])

    return <span>{displayedText}</span>
}
