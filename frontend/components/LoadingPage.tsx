import Image from "next/image";

export function LoadingPage() {
    return (
        <div className="flex w-full h-full items-center justify-center min-h-screen">
            <Image 
                src="/loading.gif" 
                alt="Loading" 
                width={200} 
                height={200}
                className="object-contain"
                unoptimized
            />
        </div>
    )
}

