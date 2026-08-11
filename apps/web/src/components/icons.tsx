import type { SVGProps } from "react";

type Props = SVGProps<SVGSVGElement>;

function IconBase({ children, ...props }: Props) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export function UploadIcon(props: Props) {
  return (
    <IconBase {...props}>
      <path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5" />
      <path d="M5 13v5a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-5" />
    </IconBase>
  );
}

export function FileIcon(props: Props) {
  return (
    <IconBase {...props}>
      <path d="M6 2.8h7l5 5V21H6z" />
      <path d="M13 2.8v5h5M9 13h6M9 17h4" />
    </IconBase>
  );
}

export function SparkIcon(props: Props) {
  return (
    <IconBase {...props}>
      <path d="m12 3 1.3 3.7L17 8l-3.7 1.3L12 13l-1.3-3.7L7 8l3.7-1.3L12 3Z" />
      <path d="m18.5 14 .7 2.3 2.3.7-2.3.7-.7 2.3-.7-2.3-2.3-.7 2.3-.7.7-2.3Z" />
      <path d="m5 13 1 2.5L8.5 17 6 18l-1 2.5L4 18l-2.5-1L4 15.5 5 13Z" />
    </IconBase>
  );
}

export function ArrowIcon(props: Props) {
  return (
    <IconBase {...props}>
      <path d="M5 12h14m-5-5 5 5-5 5" />
    </IconBase>
  );
}

export function CheckIcon(props: Props) {
  return (
    <IconBase {...props}>
      <path d="m5 12 4 4L19 6" />
    </IconBase>
  );
}

