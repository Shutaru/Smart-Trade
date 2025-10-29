// Type declarations for react-json-editor-ajrm
declare module 'react-json-editor-ajrm' {
  import { ComponentType } from 'react';
  
  export interface JSONEditorProps {
    id?: string;
    placeholder?: any;
    colors?: any;
    locale?: any;
    height?: string;
    width?: string;
    onChange?: (data: { jsObject?: any; error?: any }) => void;
    viewOnly?: boolean;
    confirmGood?: boolean;
    iconStyle?: 'triangle' | 'square' | 'circle';
    theme?: string;
    style?: React.CSSProperties;
  }
  
  const JSONEditor: ComponentType<JSONEditorProps>;
  export default JSONEditor;
}

declare module 'react-json-editor-ajrm/locale/en' {
  const locale: any;
  export default locale;
}

declare module 'react-json-editor-ajrm/locale/pt' {
  const locale: any;
  export default locale;
}
