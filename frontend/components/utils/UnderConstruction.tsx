import Image from "next/image";

export function UnderConstruction() {
    return (
        <div className="flex w-full h-full items-center justify-center">
            <Image 
                src="/underconstruction.png" 
                alt="Under Construction" 
                width={600} 
                height={600}
                className="object-contain"
            />
        </div>
    )
}