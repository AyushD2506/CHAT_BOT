declare module 'react-syntax-highlighter' {
  import * as React from 'react';
  export interface SyntaxHighlighterProps {
    language?: string;
    style?: any;
    PreTag?: any;
    children?: React.ReactNode;
    showLineNumbers?: boolean;
    wrapLongLines?: boolean;
    className?: string;
  }
  export class Prism extends React.Component<SyntaxHighlighterProps> {}
  const SyntaxHighlighter: React.ComponentType<SyntaxHighlighterProps>;
  export default SyntaxHighlighter;
}

declare module 'react-syntax-highlighter/dist/cjs/styles/prism' {
  export const oneDark: any;
}