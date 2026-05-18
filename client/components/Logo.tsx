import Image from "next/image";

type LogoProps = {
  className?: string;
};

export function Logo({ className }: LogoProps) {
  return (
    <Image
      src="/gsicon.png"
      alt="Gnostix Scribe"
      width={32}
      height={32}
      priority
      className={className}
    />
  );
}
