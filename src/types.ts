export interface DocumentMetadata {
  id: string;
  path: string;
  title: string;
  summary: string;
  tags: string[];
  departments: string[];
  docType: string;
  source?: string;
  updatedAt?: string;
  primaryCategory: string;
  secondaryCategories: string[];
}

export interface Manifest {
  documents: DocumentMetadata[];
}

export interface RouteDecision {
  targetDirs: string[];
  reason: string;
}

export interface GrepHit {
  file: string;
  lineNumber: number;
  lineText: string;
  query: string;
  matchedTerms: string[];
}

export interface Evidence {
  file: string;
  lineStart: number;
  lineEnd: number;
  score: number;
  text: string;
  matchedTerms: string[];
}

export interface SearchTrace {
  retryLevel: number;
  targetDirs: string[];
  targetFiles: string[];
  rewrittenQueries: string[];
  evidenceCount: number;
  reason: string;
}

export interface Citation {
  file: string;
  lineStart: number;
  lineEnd: number;
}

export interface Answer {
  query: string;
  answer: string;
  citations: Citation[];
  confidence: number;
  answerable: boolean;
  trace: SearchTrace[];
}

export interface Verification {
  answerable: boolean;
  confidence: number;
  evidenceFiles: string[];
  missingInfo: string[];
  reason: string;
}

export function allCategories(doc: DocumentMetadata): Set<string> {
  return new Set([doc.primaryCategory, ...doc.secondaryCategories]);
}

export function citation(evidence: Evidence): string {
  return evidence.lineStart === evidence.lineEnd
    ? `${evidence.file}:${evidence.lineStart}`
    : `${evidence.file}:${evidence.lineStart}-${evidence.lineEnd}`;
}
