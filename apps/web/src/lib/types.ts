export type FileType = "docx" | "xlsx";
export type BindingStrategy = "placeholder" | "cell" | "docx_block";

export interface CandidateProposal {
  field_id: string;
  label: string;
  block_id: string;
  anchor: string;
  confidence: number;
  source_text: string;
}

export interface TemplateBinding {
  strategy: BindingStrategy;
  placeholder?: string | null;
  cell?: string | null;
  sheet?: string | null;
  block_id?: string | null;
  anchor?: string | null;
  mode?: string | null;
}

export interface TemplateField {
  id: string;
  label: string;
  required: boolean;
  content_type: string;
  binding: TemplateBinding;
}

export interface TemplateManifest {
  template_id: string;
  name: string;
  file_type: FileType;
  original_file: string;
  document_type: string;
  fields: TemplateField[];
}

export interface TemplateRecord {
  id: string;
  name: string;
  original_filename: string;
  file_type: FileType;
  document_type: string;
  source_path: string;
  status: string;
  created_at: string;
  updated_at: string;
  manifest: TemplateManifest | null;
  analysis: Record<string, unknown> | null;
}

export interface DraftResult {
  generation_id: string;
  template_id: string;
  content: Record<string, unknown>;
  warnings: string[];
}

export interface RenderResult {
  generation_id: string;
  template_id: string;
  status: string;
  file_type: FileType;
  download_url: string;
  preview_url: string | null;
  preview_status: string | null;
  warnings: string[];
}

export interface GenerationRecord {
  id: string;
  template_id: string;
  prompt: string;
  semantic_content: Record<string, unknown>;
  output_path: string | null;
  preview_path: string | null;
  preview_status: string | null;
  status: string;
  created_at: string;
}

