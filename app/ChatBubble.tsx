// components/ChatBubble.tsx
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

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
  anger:number;
  
}) {
  return (
    <div className={cn(
      "flex flex-col gap-1 p-4 rounded-lg max-w-[80%]",
      isUser ? "ml-auto bg-blue-100" : "mr-auto bg-gray-100"
    )}>
      <p>{message}</p>
      {!isUser && (
        <div className="flex gap-2 text-sm mt-2">
          <span className="text-red-600">Anger: {anger.toFixed(1)}</span>
          <span className="text-blue-600">Sadness: {sadness.toFixed(1)}</span>
          <span className="text-blue-600">joy: {joy.toFixed(1)}</span>

        </div>
      )}
    </div>
  );
}