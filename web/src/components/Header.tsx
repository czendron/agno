import Image from "next/image";

export function Header() {
  return (
    <header className="mb-6">
      <div className="flex items-center gap-5">
        <Image
          src="/heka-hoods-logo.png"
          alt="Heka Hoods"
          width={1641}
          height={1000}
          className="h-14 w-auto"
          priority
        />
        <span className="text-2xl font-semibold uppercase tracking-[0.06em] text-brand-black">
          Box Order
        </span>
      </div>
      <p className="mt-1 text-[0.95rem] tracking-[0.01em] text-brand-gray">
        Group a job&apos;s hoods into boxes, pack them onto pallets, and generate the Dispatch
        Works Order.
      </p>
    </header>
  );
}
