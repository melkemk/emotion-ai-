import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { AlertCircle, Frown, Heart } from 'lucide-react'

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function ChatBubble({
  message,
  isUser,
  anger,
  sadness,
  joy
}: {
  message: string;
  isUser: boolean;
  sadness: number;
  joy: number;
  anger: number;
}) {
  return (
    <div className={cn(
      "flex flex-col gap-2 p-4 rounded-2xl max-w-[80%] shadow-md transition-all duration-300",
      isUser
        ? "ml-auto bg-gradient-to-r from-primary to-primary/80 text-primary-foreground"
        : "mr-auto bg-gradient-to-r from-card to-background border border-border"
    )}>
      <p className={cn(
        "text-base leading-relaxed",
        isUser ? "text-primary-foreground" : "text-foreground"
      )}>{message}</p>

      {!isUser && (
        <div className="flex gap-3 text-sm mt-1 pt-2 border-t border-border/30">
          <div className="flex items-center gap-1">
            <AlertCircle className="h-4 w-4 text-red-500" />
            <span className={cn(
              "font-medium",
              anger > 3 ? "text-red-600" : "text-foreground/80"
            )}>
              {anger.toFixed(1)}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <Frown className="h-4 w-4 text-blue-500" />
            <span className={cn(
              "font-medium",
              sadness > 3 ? "text-blue-600" : "text-foreground/80"
            )}>
              {sadness.toFixed(1)}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <Heart className="h-4 w-4 text-green-500" />
            <span className={cn(
              "font-medium",
              joy > 3 ? "text-green-600" : "text-foreground/80"
            )}>
              {joy.toFixed(1)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

