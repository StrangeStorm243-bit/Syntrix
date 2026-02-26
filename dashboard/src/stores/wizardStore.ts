import { create } from 'zustand';

export interface WizardState {
  step: number;

  // Step 1: Company info
  companyName: string;
  companyUrl: string;
  companyDescription: string;
  problemStatement: string;

  // Step 2: Ideal customer
  roleKeywords: string[];
  tweetTopics: string[];
  minFollowers: number;
  languages: string[];

  // Step 3: Twitter connection
  twitterUsername: string;
  twitterPassword: string;
  connectionTested: boolean;

  // Step 4: Persona
  personaName: string;
  personaRole: string;
  personaTone: string;
  voiceNotes: string;
  exampleReply: string;
  llmProvider: string;
  llmModel: string;
  llmApiKey: string;

  // Step 5: Outreach style
  sequenceTemplate: string;
  maxActionsPerDay: number;
  requireApproval: boolean;

  // Actions
  setStep: (step: number) => void;
  nextStep: () => void;
  prevStep: () => void;
  updateField: <K extends keyof WizardState>(key: K, value: WizardState[K]) => void;
  reset: () => void;
}

const initialState = {
  step: 0,
  companyName: '',
  companyUrl: '',
  companyDescription: '',
  problemStatement: '',
  roleKeywords: [],
  tweetTopics: [],
  minFollowers: 100,
  languages: ['en'],
  twitterUsername: '',
  twitterPassword: '',
  connectionTested: false,
  personaName: '',
  personaRole: '',
  personaTone: 'professional',
  voiceNotes: '',
  exampleReply: '',
  llmProvider: 'ollama',
  llmModel: '',
  llmApiKey: '',
  sequenceTemplate: 'engage-then-pitch',
  maxActionsPerDay: 20,
  requireApproval: true,
};

export const useWizardStore = create<WizardState>((set) => ({
  ...initialState,

  setStep: (step) => set({ step }),
  nextStep: () => set((s) => ({ step: Math.min(s.step + 1, 4) })),
  prevStep: () => set((s) => ({ step: Math.max(s.step - 1, 0) })),
  updateField: (key, value) => set({ [key]: value }),
  reset: () => set(initialState),
}));
