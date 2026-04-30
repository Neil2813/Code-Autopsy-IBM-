# Frontend Requirements - AI Legacy Modernization Copilot

## 📋 Overview

This document outlines the complete frontend requirements for the AI Legacy Modernization Copilot. The frontend must consume the FastAPI backend and provide an intuitive interface for legacy code analysis and modernization guidance.

---

## 🎯 Frontend Goals

1. **User-Friendly Interface** - Simple, clean, and intuitive UI for developers
2. **Real-Time Feedback** - Show analysis progress and status updates
3. **Interactive Exploration** - Allow users to explore analysis results
4. **Actionable Insights** - Present modernization recommendations clearly
5. **Professional Design** - Enterprise-grade UI suitable for demos and production

---

## 🏗️ Technology Stack Recommendations

### Core Framework
- **React 18+** with TypeScript
- **Vite** (alternative to Next.js for faster development)

### State Management
- **React Query (TanStack Query)** - Server state management
- **Zustand** or **Redux Toolkit** - Client state management
- **React Context** - For simple global state

### UI Framework
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - High-quality React components
- **Radix UI** - Accessible component primitives
- **Lucide React** - Icon library

### Data Visualization
- **Recharts** - Charts and graphs
- **React Flow** - Dependency graph visualization
- **D3.js** - Advanced visualizations (optional)

### Code Display
- **Monaco Editor** - Code editor (VS Code engine)
- **Prism.js** or **Highlight.js** - Syntax highlighting
- **React Diff Viewer** - Before/after code comparison

### File Handling
- **React Dropzone** - Drag-and-drop file upload
- **FilePond** - Advanced file upload with preview

### Utilities
- **Axios** or **Fetch API** - HTTP client
- **date-fns** - Date formatting
- **clsx** - Conditional class names
- **zod** - Schema validation

---

## 📱 Required Pages/Views

### 1. Landing/Home Page
**Purpose**: Welcome users and explain the product

**Components**:
- Hero section with product description
- Key features showcase
- "Get Started" CTA button
- Quick demo video or GIF
- Supported languages badges (Java, COBOL, RPG, Mainframe)

**Route**: `/`

---

### 2. Upload Page
**Purpose**: Allow users to upload code for analysis

**Components**:
- **Upload Options Tabs**:
  - File Upload (ZIP, individual files)
  - Git Repository URL
  - Code Snippet (paste code)
  
- **File Upload Area**:
  - Drag-and-drop zone
  - File browser button
  - File list with preview
  - Remove file option
  - Total size indicator
  
- **Repository Input**:
  - Git URL input field
  - Branch selection (optional)
  - Authentication fields (if needed)
  
- **Snippet Editor**:
  - Monaco editor for pasting code
  - Language selector
  - Line numbers
  
- **Upload Configuration**:
  - Project name input
  - Description textarea
  - Language selection (auto-detect or manual)
  
- **Action Buttons**:
  - Upload & Analyze button
  - Cancel button
  - Save as draft (optional)

**API Integration**:
- `POST /api/v1/upload/files`
- `POST /api/v1/upload/repository`
- `POST /api/v1/upload/snippet`

**Route**: `/upload`

---

### 3. Analysis Dashboard
**Purpose**: Show analysis progress and results

**Components**:

#### 3.1 Progress Section (During Analysis)
- **Progress Bar**: 0-100% with current stage
- **Stage Indicators**: 8 stages with checkmarks
  - Ingest (0-12.5%)
  - Parse (12.5-25%)
  - Classify (25-37.5%)
  - Analyze (37.5-50%)
  - Explain (50-62.5%)
  - Recommend (62.5-75%)
  - Validate (75-87.5%)
  - Report (87.5-100%)
- **Current Activity**: Text showing what's happening
- **Estimated Time Remaining**: Countdown timer
- **Cancel Analysis Button**: Stop the job

#### 3.2 Summary Cards (After Analysis)
- **Total Files**: Count and breakdown by language
- **Lines of Code**: Total LOC analyzed
- **Risk Score**: 0-10 with color coding
- **Maintainability Index**: 0-100 score
- **Technical Debt**: Estimated hours
- **Detected Languages**: Badges for each language

#### 3.3 Architecture Overview
- **Architecture Pattern**: Monolith, Layered, etc.
- **Frameworks Detected**: List with versions
- **Technologies Used**: Tech stack summary
- **Entry Points**: Main classes/files
- **Key Components**: Important modules

#### 3.4 File Explorer
- **Tree View**: Hierarchical file structure
- **File Icons**: Language-specific icons
- **Risk Indicators**: Color-coded dots (red, yellow, green)
- **Complexity Badges**: Show complexity score
- **Search/Filter**: Find files by name or type
- **Click to View**: Open file details

#### 3.5 Risks Panel
- **Risk List**: Sortable table
  - Title
  - Category (Security, Maintainability, etc.)
  - Severity (Critical, High, Medium, Low)
  - Affected Files
  - Recommendation
- **Filters**: By category, severity, file
- **Risk Details Modal**: Click to see full details
- **MCP Solution Badge**: Show if similar solution exists

#### 3.6 Suggestions Panel
- **Suggestion Cards**: Modernization recommendations
  - Title and description
  - Priority (1-5)
  - Effort estimate (Low, Medium, High)
  - Benefits list
  - Risks list
  - Before/After code snippets
  - MCP-based badge
- **Sort Options**: By priority, effort, impact
- **Filter Options**: By type, priority
- **Apply Suggestion**: Mark as planned/completed

#### 3.7 Dependency Graph
- **Interactive Graph**: Nodes and edges
- **Zoom/Pan Controls**: Navigate large graphs
- **Node Details**: Click to see module info
- **Highlight Paths**: Show dependencies
- **Circular Dependencies**: Highlight in red
- **Export Options**: PNG, SVG, JSON

#### 3.8 Code Viewer
- **Syntax Highlighting**: Language-specific
- **Line Numbers**: With clickable links
- **Risk Highlights**: Inline annotations
- **Suggestion Overlays**: Show recommendations
- **Before/After Toggle**: Compare versions
- **Copy Code Button**: Copy to clipboard

**API Integration**:
- `GET /api/v1/jobs/{job_id}` - Poll for status
- `GET /api/v1/jobs/{job_id}/results` - Get results
- `DELETE /api/v1/jobs/{job_id}` - Cancel job

**Route**: `/dashboard/{job_id}`

---

### 4. Query/Chat Interface
**Purpose**: Ask questions about the analyzed codebase

**Components**:
- **Chat History**: Scrollable message list
  - User questions
  - AI responses with references
  - Timestamp for each message
  
- **Input Area**:
  - Text input for questions
  - Send button
  - Suggested questions chips
  
- **Response Display**:
  - Formatted answer text
  - File references (clickable)
  - Confidence score
  - Related files list
  - Follow-up suggestions
  
- **Context Panel** (optional):
  - Show relevant code snippets
  - Highlight referenced sections

**API Integration**:
- `POST /api/v1/query` - Ask question
- `GET /api/v1/query/history/{job_id}` - Get history

**Route**: `/dashboard/{job_id}/query`

---

### 5. Report Page
**Purpose**: Generate and download analysis reports

**Components**:
- **Report Configuration**:
  - Format selection (Markdown, HTML, PDF, JSON)
  - Section selection checkboxes:
    - Summary
    - Architecture Overview
    - File Inventory
    - Risks
    - Suggestions
    - Dependency Graph
    - Code Snippets
  - Include/exclude options
  
- **Report Preview**:
  - Live preview of report content
  - Formatted display
  
- **Action Buttons**:
  - Generate Report button
  - Download button
  - Share link (optional)
  - Email report (optional)

**API Integration**:
- `POST /api/v1/report/generate` - Generate report
- `GET /api/v1/report/download/{job_id}` - Download
- `GET /api/v1/report/metadata/{job_id}` - Get metadata

**Route**: `/dashboard/{job_id}/report`

---

### 6. Job History Page
**Purpose**: View past analysis jobs

**Components**:
- **Job List Table**:
  - Job ID
  - Project name
  - Upload date
  - Status (Completed, Failed, In Progress)
  - Languages detected
  - Risk score
  - Actions (View, Delete, Re-analyze)
  
- **Filters**:
  - By status
  - By date range
  - By language
  
- **Search**: Find by project name or ID
- **Pagination**: Navigate through jobs

**API Integration**:
- `GET /api/v1/jobs` - List all jobs
- `DELETE /api/v1/jobs/{job_id}` - Delete job

**Route**: `/history`

---

### 7. Settings Page (Optional)
**Purpose**: Configure user preferences

**Components**:
- **API Configuration**:
  - Backend URL
  - API key (if needed)
  
- **Analysis Preferences**:
  - Default analysis options
  - Language preferences
  
- **UI Preferences**:
  - Theme (Light/Dark)
  - Font size
  - Code editor theme
  
- **Notifications**:
  - Email notifications
  - Browser notifications

**Route**: `/settings`

---

## 🎨 UI/UX Requirements

### Design Principles
1. **Clean & Modern**: Minimalist design with focus on content
2. **Responsive**: Works on desktop, tablet, mobile
3. **Accessible**: WCAG 2.1 AA compliance
4. **Fast**: Optimized performance, lazy loading
5. **Intuitive**: Clear navigation, helpful tooltips

### Color Scheme
- **Primary**: Blue (#3B82F6) - Trust, technology
- **Success**: Green (#10B981) - Low risk, completed
- **Warning**: Yellow (#F59E0B) - Medium risk, attention
- **Danger**: Red (#EF4444) - High risk, critical
- **Neutral**: Gray (#6B7280) - Text, borders

### Typography
- **Headings**: Inter or Poppins (bold, clear)
- **Body**: Inter or System UI (readable)
- **Code**: JetBrains Mono or Fira Code (monospace)

### Layout
- **Header**: Logo, navigation, user menu
- **Sidebar**: Navigation menu (collapsible)
- **Main Content**: Primary content area
- **Footer**: Links, version, copyright

---

## 🔌 API Integration Requirements

### HTTP Client Setup
```typescript
// api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use((config) => {
  // Add auth token if needed
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle errors globally
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default apiClient;
```

### API Service Functions
```typescript
// api/services.ts
import apiClient from './client';

export const uploadService = {
  uploadFiles: (files: File[]) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    return apiClient.post('/api/v1/upload/files', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  uploadRepository: (url: string) => {
    return apiClient.post('/api/v1/upload/repository', { repo_url: url });
  },
  
  uploadSnippet: (code: string, language: string) => {
    return apiClient.post('/api/v1/upload/snippet', { content: code, language });
  },
};

export const analysisService = {
  startAnalysis: (jobId: string, options: any) => {
    return apiClient.post('/api/v1/analyze', { job_id: jobId, analysis_options: options });
  },
  
  getJobStatus: (jobId: string) => {
    return apiClient.get(`/api/v1/jobs/${jobId}`);
  },
  
  getResults: (jobId: string) => {
    return apiClient.get(`/api/v1/jobs/${jobId}/results`);
  },
  
  cancelJob: (jobId: string) => {
    return apiClient.delete(`/api/v1/jobs/${jobId}`);
  },
};

export const queryService = {
  askQuestion: (jobId: string, question: string) => {
    return apiClient.post('/api/v1/query', { job_id: jobId, question });
  },
  
  getHistory: (jobId: string) => {
    return apiClient.get(`/api/v1/query/history/${jobId}`);
  },
};

export const reportService = {
  generateReport: (jobId: string, format: string, sections: string[]) => {
    return apiClient.post('/api/v1/report/generate', { job_id: jobId, format, sections });
  },
  
  downloadReport: (jobId: string) => {
    return apiClient.get(`/api/v1/report/download/${jobId}`, { responseType: 'blob' });
  },
};
```

### React Query Hooks
```typescript
// hooks/useAnalysis.ts
import { useQuery, useMutation } from '@tanstack/react-query';
import { analysisService } from '@/api/services';

export const useJobStatus = (jobId: string) => {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => analysisService.getJobStatus(jobId),
    refetchInterval: (data) => {
      // Poll every 2 seconds if job is processing
      return data?.status === 'processing' ? 2000 : false;
    },
  });
};

export const useAnalysisResults = (jobId: string) => {
  return useQuery({
    queryKey: ['results', jobId],
    queryFn: () => analysisService.getResults(jobId),
    enabled: !!jobId,
  });
};

export const useStartAnalysis = () => {
  return useMutation({
    mutationFn: ({ jobId, options }: any) => 
      analysisService.startAnalysis(jobId, options),
  });
};
```

---

## 📊 State Management

### Global State (Zustand Example)
```typescript
// store/useAppStore.ts
import { create } from 'zustand';

interface AppState {
  currentJobId: string | null;
  setCurrentJobId: (id: string | null) => void;
  
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentJobId: null,
  setCurrentJobId: (id) => set({ currentJobId: id }),
  
  theme: 'light',
  toggleTheme: () => set((state) => ({ 
    theme: state.theme === 'light' ? 'dark' : 'light' 
  })),
  
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));
```

---

## 🧩 Key Components to Build

### 1. FileUploader Component
- Drag-and-drop zone
- File list with preview
- Progress indicators
- Error handling

### 2. ProgressTracker Component
- 8-stage progress bar
- Stage indicators with icons
- Current activity text
- Time remaining

### 3. RiskCard Component
- Risk title and description
- Severity badge
- Affected files list
- Recommendation text
- MCP solution indicator

### 4. SuggestionCard Component
- Suggestion title
- Priority badge
- Effort estimate
- Benefits/risks lists
- Code diff viewer
- Action buttons

### 5. DependencyGraph Component
- Interactive graph visualization
- Zoom/pan controls
- Node selection
- Path highlighting
- Export functionality

### 6. CodeViewer Component
- Syntax highlighting
- Line numbers
- Risk annotations
- Copy button
- Full-screen mode

### 7. ChatInterface Component
- Message list
- Input field
- Suggested questions
- File references
- Loading states

### 8. ReportPreview Component
- Formatted report display
- Section navigation
- Export options
- Print functionality

---

## 🔒 Security Considerations

1. **Input Validation**: Validate all user inputs
2. **XSS Prevention**: Sanitize displayed content
3. **CSRF Protection**: Use CSRF tokens
4. **Secure Storage**: Don't store sensitive data in localStorage
5. **HTTPS Only**: Enforce HTTPS in production
6. **API Key Protection**: Never expose API keys in frontend code

---

## ⚡ Performance Optimization

1. **Code Splitting**: Lazy load routes and components
2. **Image Optimization**: Use Next.js Image or similar
3. **Caching**: Cache API responses with React Query
4. **Virtualization**: Use react-window for large lists
5. **Debouncing**: Debounce search and filter inputs
6. **Memoization**: Use React.memo and useMemo
7. **Bundle Size**: Monitor and optimize bundle size

---

## 📱 Responsive Design Breakpoints

```css
/* Tailwind CSS breakpoints */
sm: 640px   /* Small devices (phones) */
md: 768px   /* Medium devices (tablets) */
lg: 1024px  /* Large devices (desktops) */
xl: 1280px  /* Extra large devices */
2xl: 1536px /* 2X large devices */
```

### Mobile Considerations
- Collapsible sidebar
- Simplified navigation
- Touch-friendly buttons
- Responsive tables (horizontal scroll or cards)
- Bottom navigation bar (optional)

---

## 🧪 Testing Requirements

### Unit Tests
- Component rendering
- User interactions
- State management
- Utility functions

### Integration Tests
- API integration
- Form submissions
- Navigation flows
- Error handling

### E2E Tests (Playwright/Cypress)
- Complete user workflows
- Upload → Analysis → Results
- Query interface
- Report generation

---

## 📦 Project Structure

```
frontend/
├── public/
│   ├── favicon.ico
│   └── images/
├── src/
│   ├── app/                    # Next.js app directory (or pages/)
│   │   ├── layout.tsx
│   │   ├── page.tsx           # Home page
│   │   ├── upload/
│   │   ├── dashboard/
│   │   ├── history/
│   │   └── settings/
│   ├── components/
│   │   ├── ui/                # shadcn/ui components
│   │   ├── layout/            # Layout components
│   │   ├── upload/            # Upload-related components
│   │   ├── dashboard/         # Dashboard components
│   │   ├── query/             # Query interface components
│   │   └── report/            # Report components
│   ├── lib/
│   │   ├── api/               # API client and services
│   │   ├── hooks/             # Custom React hooks
│   │   ├── store/             # State management
│   │   ├── utils/             # Utility functions
│   │   └── types/             # TypeScript types
│   ├── styles/
│   │   └── globals.css        # Global styles
│   └── config/
│       └── constants.ts       # App constants
├── .env.local                 # Environment variables
├── .env.example               # Environment template
├── next.config.js             # Next.js config
├── tailwind.config.js         # Tailwind config
├── tsconfig.json              # TypeScript config
├── package.json
└── README.md
```

---

## 🚀 Getting Started (For Frontend Developers)

### 1. Setup
```bash
# Create Next.js app with TypeScript
npx create-next-app@latest frontend --typescript --tailwind --app

cd frontend

# Install dependencies
npm install @tanstack/react-query zustand axios
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu
npm install lucide-react clsx tailwind-merge
npm install react-dropzone monaco-editor
npm install recharts react-flow-renderer
npm install date-fns zod
```

### 2. Configure Environment
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=AI Legacy Modernization Copilot
```

### 3. Run Development Server
```bash
npm run dev
# Open http://localhost:3000
```

---

## 📋 Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Set up Next.js project with TypeScript
- [ ] Configure Tailwind CSS
- [ ] Install and configure shadcn/ui
- [ ] Set up API client with Axios
- [ ] Configure React Query
- [ ] Create basic layout (header, sidebar, footer)
- [ ] Implement routing structure

### Phase 2: Upload Flow (Week 2)
- [ ] Build file upload component
- [ ] Implement drag-and-drop
- [ ] Add repository URL input
- [ ] Create code snippet editor
- [ ] Integrate upload APIs
- [ ] Add upload validation
- [ ] Implement error handling

### Phase 3: Dashboard (Week 3)
- [ ] Create progress tracker
- [ ] Build summary cards
- [ ] Implement file explorer
- [ ] Create risks panel
- [ ] Build suggestions panel
- [ ] Add code viewer
- [ ] Integrate job status polling

### Phase 4: Visualization (Week 4)
- [ ] Implement dependency graph
- [ ] Add architecture overview
- [ ] Create risk heatmap
- [ ] Build complexity charts
- [ ] Add interactive tooltips

### Phase 5: Query & Report (Week 5)
- [ ] Build chat interface
- [ ] Implement query API integration
- [ ] Create report configuration
- [ ] Add report preview
- [ ] Implement report download
- [ ] Add export options

### Phase 6: Polish & Testing (Week 6)
- [ ] Add loading states
- [ ] Implement error boundaries
- [ ] Add animations and transitions
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Optimize performance
- [ ] Responsive design testing
- [ ] Accessibility audit

---

## 🎯 Success Criteria

✅ **Functional**:
- All API endpoints integrated
- Upload flow works end-to-end
- Analysis results display correctly
- Query interface responds accurately
- Reports generate successfully

✅ **Performance**:
- Initial load < 3 seconds
- API responses handled smoothly
- Large datasets render efficiently
- No memory leaks

✅ **UX**:
- Intuitive navigation
- Clear feedback on actions
- Helpful error messages
- Responsive on all devices
- Accessible to all users

✅ **Code Quality**:
- TypeScript strict mode
- ESLint/Prettier configured
- Component tests written
- Code documented
- Git workflow followed

---

## 📚 Resources

### Documentation
- [React Docs](https://react.dev/)
- [Next.js Docs](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com/)
- [React Query](https://tanstack.com/query/latest)

### Design Inspiration
- [Vercel Dashboard](https://vercel.com/dashboard)
- [GitHub Code Analysis](https://github.com/features/code-review)
- [SonarQube UI](https://www.sonarqube.org/)

---

## 🤝 Backend Integration Points

### Required Backend Endpoints
All endpoints documented in `Backend/README.md`:
- ✅ POST /api/v1/upload/files
- ✅ POST /api/v1/upload/repository
- ✅ POST /api/v1/upload/snippet
- ✅ POST /api/v1/analyze
- ✅ GET /api/v1/jobs/{job_id}
- ✅ GET /api/v1/jobs/{job_id}/results
- ✅ DELETE /api/v1/jobs/{job_id}
- ✅ POST /api/v1/query
- ✅ GET /api/v1/query/history/{job_id}
- ✅ POST /api/v1/report/generate
- ✅ GET /api/v1/report/download/{job_id}
- ✅ GET /api/v1/health

### Data Models
All TypeScript interfaces should match Pydantic schemas in `Backend/DATA_MODELS.md`

---

## 🎉 Conclusion

This frontend will provide a professional, user-friendly interface for the AI Legacy Modernization Copilot. The design prioritizes clarity, usability, and actionable insights to help developers modernize legacy codebases efficiently.

**Key Principles**:
- Clean, modern design
- Real-time feedback
- Interactive exploration
- Actionable recommendations
- Production-ready quality

**Ready to build an amazing frontend! 🚀**