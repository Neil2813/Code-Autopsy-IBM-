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

## 📱 Complete Page Structure

### Authentication Pages

#### 1. Login Page
**Purpose**: User authentication and access control

**Components**:
- **Login Form**:
  - Email/Username input field
  - Password input field (with show/hide toggle)
  - "Remember me" checkbox
  - "Forgot password?" link
  - Login button
  - Social login options (Google, GitHub, Microsoft - optional)
  
- **Additional Elements**:
  - Logo and branding
  - Welcome message
  - "Don't have an account? Sign up" link
  - Terms of service and privacy policy links
  - Loading state during authentication
  - Error messages display

**API Integration**:
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/social` - Social authentication (optional)

**Route**: `/login`

**Features**:
- Form validation (email format, password requirements)
- Error handling (invalid credentials, account locked)
- Session management
- Redirect to dashboard after successful login
- Remember me functionality

---

#### 2. Register/Sign Up Page
**Purpose**: New user account creation

**Components**:
- **Registration Form**:
  - Full name input
  - Email address input
  - Username input (optional)
  - Password input (with strength indicator)
  - Confirm password input
  - Organization/Company name (optional)
  - Role selection (Developer, Architect, Manager)
  - Terms and conditions checkbox
  - Sign up button
  
- **Additional Elements**:
  - Logo and branding
  - "Already have an account? Login" link
  - Password requirements tooltip
  - Email verification notice
  - Social sign-up options (optional)

**API Integration**:
- `POST /api/v1/auth/register` - Create new account
- `POST /api/v1/auth/verify-email` - Email verification

**Route**: `/register` or `/signup`

**Features**:
- Real-time form validation
- Password strength meter
- Email format validation
- Username availability check
- Terms acceptance requirement
- Email verification flow
- Redirect to onboarding or dashboard

---

#### 3. Forgot Password Page
**Purpose**: Password recovery

**Components**:
- **Password Reset Form**:
  - Email input field
  - Submit button
  - Back to login link
  
- **Success Message**:
  - Confirmation that reset email was sent
  - Instructions to check email
  - Resend email option

**API Integration**:
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset password with token

**Route**: `/forgot-password`

---

#### 4. Reset Password Page
**Purpose**: Set new password after reset request

**Components**:
- **New Password Form**:
  - New password input (with strength indicator)
  - Confirm new password input
  - Submit button
  - Password requirements display

**API Integration**:
- `POST /api/v1/auth/reset-password` - Set new password

**Route**: `/reset-password?token=xxx`

---

### Main Application Pages

#### 5. Landing/Home Page
**Purpose**: Welcome users and explain the product

**Components**:
- Hero section with product description
- Key features showcase
- "Get Started" CTA button
- Quick demo video or GIF
- Supported languages badges (Java, COBOL, RPG, Mainframe)
- IBM watsonx.ai integration highlight
- Customer testimonials (optional)
- Pricing information (optional)

**Route**: `/`

**Access**: Public (no authentication required)

---

#### 6. Dashboard/Overview Page
**Purpose**: Main hub after login, show user's projects and recent activity

**Components**:
- **Welcome Section**:
  - User greeting
  - Quick stats (total projects, analyses completed, time saved)
  
- **Recent Projects**:
  - List of recent analysis jobs
  - Quick access cards with status
  - "View All" link to history page
  
- **Quick Actions**:
  - "New Analysis" button
  - "Upload Code" button
  - "View Documentation" link
  
- **Activity Feed**:
  - Recent analyses
  - Completed reports
  - System notifications
  
- **Statistics Cards**:
  - Total analyses this month
  - Average risk score
  - Lines of code analyzed
  - Time saved

**API Integration**:
- `GET /api/v1/dashboard/stats` - Dashboard statistics
- `GET /api/v1/jobs?limit=5` - Recent jobs

**Route**: `/dashboard`

**Access**: Authenticated users only

---

#### 7. Upload Page
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

**Access**: Authenticated users only

---

#### 8. Analysis Dashboard
**Purpose**: Show analysis progress and results

**Components**:

##### 8.1 Progress Section (During Analysis)
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

##### 8.2 Summary Cards (After Analysis)
- **Total Files**: Count and breakdown by language
- **Lines of Code**: Total LOC analyzed
- **Risk Score**: 0-10 with color coding
- **Maintainability Index**: 0-100 score
- **Technical Debt**: Estimated hours
- **Detected Languages**: Badges for each language

##### 8.3 Architecture Overview
- **Architecture Pattern**: Monolith, Layered, etc.
- **Frameworks Detected**: List with versions
- **Technologies Used**: Tech stack summary
- **Entry Points**: Main classes/files
- **Key Components**: Important modules

##### 8.4 File Explorer
- **Tree View**: Hierarchical file structure
- **File Icons**: Language-specific icons
- **Risk Indicators**: Color-coded dots (red, yellow, green)
- **Complexity Badges**: Show complexity score
- **Search/Filter**: Find files by name or type
- **Click to View**: Open file details

##### 8.5 Risks Panel
- **Risk List**: Sortable table
  - Title
  - Category (Security, Maintainability, etc.)
  - Severity (Critical, High, Medium, Low)
  - Affected Files
  - Recommendation
- **Filters**: By category, severity, file
- **Risk Details Modal**: Click to see full details
- **MCP Solution Badge**: Show if similar solution exists

##### 8.6 Suggestions Panel
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

##### 8.7 Dependency Graph
- **Interactive Graph**: Nodes and edges
- **Zoom/Pan Controls**: Navigate large graphs
- **Node Details**: Click to see module info
- **Highlight Paths**: Show dependencies
- **Circular Dependencies**: Highlight in red
- **Export Options**: PNG, SVG, JSON

##### 8.8 Code Viewer
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

**Route**: `/analysis/{job_id}`

**Access**: Authenticated users only

---

#### 9. Query/Chat Interface
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

**Route**: `/analysis/{job_id}/query`

**Access**: Authenticated users only

---

#### 10. Report Page
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

**Route**: `/analysis/{job_id}/report`

**Access**: Authenticated users only

---

#### 11. Job History Page
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
- **Bulk Actions**: Delete multiple jobs

**API Integration**:
- `GET /api/v1/jobs` - List all jobs
- `DELETE /api/v1/jobs/{job_id}` - Delete job

**Route**: `/history`

**Access**: Authenticated users only

---

#### 12. User Profile Page
**Purpose**: Manage user account and preferences

**Components**:
- **Profile Information**:
  - Profile picture upload
  - Full name
  - Email address
  - Username
  - Organization
  - Role
  - Edit button
  
- **Account Settings**:
  - Change password
  - Two-factor authentication
  - Email notifications
  - Session management
  
- **Usage Statistics**:
  - Total analyses
  - Total lines analyzed
  - Time saved
  - Account creation date
  
- **Danger Zone**:
  - Delete account button
  - Export data button

**API Integration**:
- `GET /api/v1/user/profile` - Get profile
- `PUT /api/v1/user/profile` - Update profile
- `POST /api/v1/user/change-password` - Change password
- `DELETE /api/v1/user/account` - Delete account

**Route**: `/profile`

**Access**: Authenticated users only

---

#### 13. Settings Page
**Purpose**: Configure application preferences

**Components**:
- **General Settings**:
  - Language preference
  - Timezone
  - Date format
  
- **API Configuration**:
  - Backend URL (for advanced users)
  - API key management
  
- **Analysis Preferences**:
  - Default analysis options
  - Language preferences
  - Auto-start analysis
  
- **UI Preferences**:
  - Theme (Light/Dark/Auto)
  - Font size
  - Code editor theme
  - Sidebar position
  
- **Notifications**:
  - Email notifications
  - Browser notifications
  - Notification frequency
  
- **Privacy**:
  - Data retention settings
  - Analytics opt-out
  - Cookie preferences

**API Integration**:
- `GET /api/v1/user/settings` - Get settings
- `PUT /api/v1/user/settings` - Update settings

**Route**: `/settings`

**Access**: Authenticated users only

---

#### 14. Documentation Page
**Purpose**: Help users understand the platform

**Components**:
- **Getting Started Guide**:
  - Quick start tutorial
  - Video walkthrough
  - Step-by-step instructions
  
- **Feature Documentation**:
  - Upload methods
  - Analysis options
  - Understanding results
  - Query interface
  - Report generation
  
- **API Documentation**:
  - API reference
  - Code examples
  - Integration guides
  
- **FAQ Section**:
  - Common questions
  - Troubleshooting
  - Best practices
  
- **Search Functionality**:
  - Search docs
  - Filter by category

**Route**: `/docs`

**Access**: Public or authenticated

---

#### 15. About Page
**Purpose**: Information about the platform

**Components**:
- **Product Information**:
  - What is AI Legacy Modernization Copilot
  - Key features
  - Technology stack
  
- **IBM watsonx.ai Integration**:
  - How we use watsonx.ai
  - Benefits of IBM technology
  - Enterprise features
  
- **Team Information** (optional):
  - About the team
  - Contact information
  
- **Version Information**:
  - Current version
  - Release notes
  - Changelog

**Route**: `/about`

**Access**: Public

---

#### 16. Contact/Support Page
**Purpose**: User support and feedback

**Components**:
- **Contact Form**:
  - Name
  - Email
  - Subject
  - Message
  - Attachment upload
  - Submit button
  
- **Support Options**:
  - Email support
  - Live chat (optional)
  - Knowledge base link
  - Community forum link
  
- **Feedback Form**:
  - Feature requests
  - Bug reports
  - General feedback

**API Integration**:
- `POST /api/v1/support/contact` - Submit contact form
- `POST /api/v1/support/feedback` - Submit feedback

**Route**: `/contact` or `/support`

**Access**: Public or authenticated

---

#### 17. Error Pages

##### 404 - Not Found
**Components**:
- Error message
- "Page not found" illustration
- Back to home button
- Search functionality
- Suggested pages

**Route**: `/404`

##### 500 - Server Error
**Components**:
- Error message
- "Something went wrong" illustration
- Retry button
- Contact support link
- Error ID for support

**Route**: `/500`

##### 403 - Forbidden
**Components**:
- Access denied message
- Login prompt
- Contact admin link

**Route**: `/403`

---

## 🗺️ Complete Routing Structure

```typescript
// routes.ts
export const routes = {
  // Public routes
  home: '/',
  login: '/login',
  register: '/register',
  forgotPassword: '/forgot-password',
  resetPassword: '/reset-password',
  about: '/about',
  contact: '/contact',
  docs: '/docs',
  
  // Protected routes (require authentication)
  dashboard: '/dashboard',
  upload: '/upload',
  analysis: '/analysis/:jobId',
  analysisQuery: '/analysis/:jobId/query',
  analysisReport: '/analysis/:jobId/report',
  history: '/history',
  profile: '/profile',
  settings: '/settings',
  
  // Error routes
  notFound: '/404',
  serverError: '/500',
  forbidden: '/403',
};
```

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
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### API Service Functions
```typescript
// api/services.ts
import apiClient from './client';

export const authService = {
  login: (email: string, password: string) => {
    return apiClient.post('/api/v1/auth/login', { email, password });
  },
  
  register: (data: RegisterData) => {
    return apiClient.post('/api/v1/auth/register', data);
  },
  
  logout: () => {
    return apiClient.post('/api/v1/auth/logout');
  },
  
  forgotPassword: (email: string) => {
    return apiClient.post('/api/v1/auth/forgot-password', { email });
  },
  
  resetPassword: (token: string, password: string) => {
    return apiClient.post('/api/v1/auth/reset-password', { token, password });
  },
};

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

export const userService = {
  getProfile: () => {
    return apiClient.get('/api/v1/user/profile');
  },
  
  updateProfile: (data: ProfileData) => {
    return apiClient.put('/api/v1/user/profile', data);
  },
  
  changePassword: (oldPassword: string, newPassword: string) => {
    return apiClient.post('/api/v1/user/change-password', { oldPassword, newPassword });
  },
  
  getSettings: () => {
    return apiClient.get('/api/v1/user/settings');
  },
  
  updateSettings: (settings: any) => {
    return apiClient.put('/api/v1/user/settings', settings);
  },
};
```

### React Query Hooks
```typescript
// hooks/useAuth.ts
import { useMutation, useQuery } from '@tanstack/react-query';
import { authService } from '@/api/services';

export const useLogin = () => {
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authService.login(email, password),
    onSuccess: (data) => {
      localStorage.setItem('token', data.token);
      window.location.href = '/dashboard';
    },
  });
};

export const useRegister = () => {
  return useMutation({
    mutationFn: (data: RegisterData) => authService.register(data),
  });
};

// hooks/useAnalysis.ts
import { useQuery, useMutation } from '@tanstack/react-query';
import { analysisService } from '@/api/services';

export const useJobStatus = (jobId: string) => {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => analysisService.getJobStatus(jobId),
    refetchInterval: (data) => {
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

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

interface AppState {
  // Auth state
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  logout: () => void;
  
  // Current job
  currentJobId: string | null;
  setCurrentJobId: (id: string | null) => void;
  
  // UI state
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Auth
  user: null,
  isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  logout: () => {
    localStorage.removeItem('token');
    set({ user: null, isAuthenticated: false });
  },
  
  // Job
  currentJobId: null,
  setCurrentJobId: (id) => set({ currentJobId: id }),
  
  // UI
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

### Authentication Components
1. **LoginForm** - Email/password login
2. **RegisterForm** - User registration
3. **ForgotPasswordForm** - Password recovery
4. **ResetPasswordForm** - New password setup
5. **ProtectedRoute** - Route guard for authenticated pages

### Core Components
6. **FileUploader** - Drag-and-drop upload
7. **ProgressTracker** - 8-stage progress bar
8. **RiskCard** - Risk display
9. **SuggestionCard** - Modernization suggestions
10. **DependencyGraph** - Interactive graph
11. **CodeViewer** - Syntax-highlighted code
12. **ChatInterface** - Q&A interface
13. **ReportPreview** - Report display

### Layout Components
14. **Header** - Top navigation
15. **Sidebar** - Side navigation
16. **Footer** - Bottom info
17. **UserMenu** - Profile dropdown

---

## 🔒 Security Considerations

1. **Authentication**: JWT token-based auth
2. **Input Validation**: Validate all user inputs
3. **XSS Prevention**: Sanitize displayed content
4. **CSRF Protection**: Use CSRF tokens
5. **Secure Storage**: Use httpOnly cookies for tokens
6. **HTTPS Only**: Enforce HTTPS in production
7. **API Key Protection**: Never expose keys in frontend

---

## ⚡ Performance Optimization

1. **Code Splitting**: Lazy load routes
2. **Image Optimization**: Optimize images
3. **Caching**: Cache API responses
4. **Virtualization**: Use react-window for large lists
5. **Debouncing**: Debounce search inputs
6. **Memoization**: Use React.memo and useMemo
7. **Bundle Size**: Monitor and optimize

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

---

## 📦 Project Structure

```
frontend/
├── public/
│   ├── favicon.ico
│   └── images/
├── src/
│   ├── app/                    # Next.js app directory
│   │   ├── layout.tsx
│   │   ├── page.tsx           # Home page
│   │   ├── login/
│   │   ├── register/
│   │   ├── forgot-password/
│   │   ├── dashboard/
│   │   ├── upload/
│   │   ├── analysis/
│   │   ├── history/
│   │   ├── profile/
│   │   ├── settings/
│   │   ├── docs/
│   │   ├── about/
│   │   └── contact/
│   ├── components/
│   │   ├── ui/                # shadcn/ui components
│   │   ├── auth/              # Auth components
│   │   ├── layout/            # Layout components
│   │   ├── upload/            # Upload components
│   │   ├── dashboard/         # Dashboard components
│   │   ├── query/             # Query components
│   │   └── report/            # Report components
│   ├── lib/
│   │   ├── api/               # API client
│   │   ├── hooks/             # Custom hooks

│   │   ├── store/              # State management
│   │   ├── utils/              # Utility functions
│   │   └── types/              # TypeScript types
│   ├── styles/
│   │   └── globals.css
│   ├── config/
│   │   └── constants.ts
│   └── middleware.ts           # Next.js middleware
├── .env.local
├── .env.example
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

## 🧪 Testing Requirements

### Unit Testing
- **Framework**: Jest + React Testing Library
- **Coverage Target**: 80%+ for critical components
- **Test Files**: Co-located with components (`*.test.tsx`)

### E2E Testing
- **Framework**: Playwright or Cypress
- **Critical Flows**:
  - User authentication flow
  - File upload and analysis
  - Query interaction
  - Report generation

### Testing Structure
```
frontend/
├── __tests__/
│   ├── unit/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── utils/
│   ├── integration/
│   │   └── api/
│   └── e2e/
│       ├── auth.spec.ts
│       ├── upload.spec.ts
│       ├── analysis.spec.ts
│       └── query.spec.ts
```

## 🚀 Deployment Considerations

### Build Configuration
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:e2e": "playwright test",
    "type-check": "tsc --noEmit"
  }
}
```

### Environment Variables
```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=v1

# Authentication
NEXT_PUBLIC_AUTH_ENABLED=true
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_CHAT=true
NEXT_PUBLIC_MAX_FILE_SIZE=104857600

# Analytics (Optional)
NEXT_PUBLIC_GA_ID=
NEXT_PUBLIC_SENTRY_DSN=
```

### Docker Configuration
```dockerfile
# Dockerfile
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
      - NEXT_PUBLIC_API_VERSION=v1
    depends_on:
      - backend
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

## 📚 Documentation Requirements

### Component Documentation
- Use JSDoc comments for all components
- Include prop types and descriptions
- Provide usage examples

Example:
```typescript
/**
 * FileUploader Component
 * 
 * Handles file upload with drag-and-drop support and progress tracking.
 * 
 * @component
 * @example
 * ```tsx
 * <FileUploader
 *   onUploadComplete={(files) => console.log(files)}
 *   maxSize={100 * 1024 * 1024}
 *   acceptedTypes={['.zip', '.tar.gz']}
 * />
 * ```
 */
export const FileUploader: React.FC<FileUploaderProps> = ({ ... }) => {
  // Component implementation
}
```

### Storybook (Optional but Recommended)
```bash
npm install --save-dev @storybook/react @storybook/addon-essentials
```

Create stories for key components:
```typescript
// components/ui/Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Click me',
  },
};
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example
```yaml
# .github/workflows/frontend.yml
name: Frontend CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run linter
      run: npm run lint
    
    - name: Type check
      run: npm run type-check
    
    - name: Run tests
      run: npm test -- --coverage
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage/lcov.info
  
  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Build application
      run: npm run build
      env:
        NEXT_PUBLIC_API_URL: ${{ secrets.API_URL }}
    
    - name: Upload build artifacts
      uses: actions/upload-artifact@v3
      with:
        name: build
        path: .next/
```

## 🎯 Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Set up Next.js project with TypeScript
- [ ] Configure Tailwind CSS and shadcn/ui
- [ ] Implement basic routing structure
- [ ] Create layout components (Header, Footer, Sidebar)
- [ ] Set up API client and authentication

### Phase 2: Core Features (Week 3-4)
- [ ] Implement authentication pages (Login, Register, Password Reset)
- [ ] Build file upload functionality
- [ ] Create dashboard with summary cards
- [ ] Implement job history page
- [ ] Add basic error handling

### Phase 3: Analysis Features (Week 5-6)
- [ ] Build analysis dashboard with real-time updates
- [ ] Implement code viewer with syntax highlighting
- [ ] Create dependency graph visualization
- [ ] Add risk and suggestion panels
- [ ] Implement file explorer

### Phase 4: Advanced Features (Week 7-8)
- [ ] Build query/chat interface with streaming
- [ ] Implement report generation and export
- [ ] Add data visualization charts
- [ ] Create settings and profile pages
- [ ] Implement documentation pages

### Phase 5: Polish & Testing (Week 9-10)
- [ ] Write comprehensive unit tests
- [ ] Implement E2E tests for critical flows
- [ ] Performance optimization
- [ ] Accessibility improvements
- [ ] Cross-browser testing
- [ ] Mobile responsiveness refinement

### Phase 6: Deployment (Week 11-12)
- [ ] Set up CI/CD pipeline
- [ ] Configure production environment
- [ ] Deploy to staging
- [ ] User acceptance testing
- [ ] Deploy to production
- [ ] Monitor and fix issues

## 🔧 Development Guidelines

### Code Style
- Use ESLint and Prettier for consistent formatting
- Follow Airbnb React/TypeScript style guide
- Use functional components with hooks
- Prefer composition over inheritance

### Git Workflow
- Use feature branches (`feature/component-name`)
- Write descriptive commit messages
- Create pull requests for code review
- Squash commits before merging

### Component Guidelines
- Keep components small and focused (< 200 lines)
- Extract reusable logic into custom hooks
- Use TypeScript for type safety
- Write tests for all components

### Performance Best Practices
- Use React.memo for expensive components
- Implement code splitting with dynamic imports
- Optimize images with Next.js Image component
- Use React Query for efficient data fetching
- Implement virtual scrolling for large lists

## 📊 Monitoring & Analytics

### Error Tracking
```typescript
// lib/monitoring/sentry.ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 1.0,
});
```

### Analytics
```typescript
// lib/analytics/gtag.ts
export const pageview = (url: string) => {
  window.gtag('config', process.env.NEXT_PUBLIC_GA_ID, {
    page_path: url,
  });
};

export const event = ({ action, category, label, value }: {
  action: string;
  category: string;
  label: string;
  value?: number;
}) => {
  window.gtag('event', action, {
    event_category: category,
    event_label: label,
    value: value,
  });
};
```

### Performance Monitoring
```typescript
// lib/monitoring/performance.ts
export const reportWebVitals = (metric: any) => {
  if (metric.label === 'web-vital') {
    // Send to analytics
    console.log(metric);
  }
};
```

## 🎨 Design System

### Component Variants
```typescript
// Example: Button variants
const buttonVariants = {
  variant: {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-900',
    outline: 'border-2 border-blue-600 text-blue-600 hover:bg-blue-50',
    ghost: 'hover:bg-gray-100 text-gray-700',
    danger: 'bg-red-600 hover:bg-red-700 text-white',
  },
  size: {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  },
};
```

### Spacing System
```typescript
// Consistent spacing scale
const spacing = {
  xs: '0.25rem',  // 4px
  sm: '0.5rem',   // 8px
  md: '1rem',     // 16px
  lg: '1.5rem',   // 24px
  xl: '2rem',     // 32px
  '2xl': '3rem',  // 48px
  '3xl': '4rem',  // 64px
};
```

## 🌐 Internationalization (i18n)

### Setup (Optional for future)
```typescript
// lib/i18n/config.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: {
        translation: require('./locales/en.json'),
      },
      es: {
        translation: require('./locales/es.json'),
      },
    },
    lng: 'en',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
```

## 🔐 Security Checklist

- [ ] Implement CSRF protection
- [ ] Sanitize user inputs
- [ ] Use HTTPS in production
- [ ] Implement rate limiting on API calls
- [ ] Secure authentication tokens (httpOnly cookies)
- [ ] Implement Content Security Policy (CSP)
- [ ] Regular dependency updates
- [ ] XSS prevention
- [ ] SQL injection prevention (backend)
- [ ] Implement proper CORS policies

## 📱 Progressive Web App (PWA) Features

### Manifest
```json
// public/manifest.json
{
  "name": "AI Legacy Modernization Copilot",
  "short_name": "IBM BOB",
  "description": "AI-powered legacy code modernization platform",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#0f62fe",
  "icons": [
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### Service Worker (Optional)
```typescript
// public/sw.js
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('v1').then((cache) => {
      return cache.addAll([
        '/',
        '/styles/globals.css',
        '/offline.html',
      ]);
    })
  );
});
```

## 🎓 Learning Resources

### Recommended Documentation
- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com)
- [React Query](https://tanstack.com/query/latest)
- [Zustand](https://github.com/pmndrs/zustand)

### Best Practices
- [React Best Practices](https://react.dev/learn/thinking-in-react)
- [Next.js Best Practices](https://nextjs.org/docs/pages/building-your-application/deploying/production-checklist)
- [TypeScript Best Practices](https://www.typescriptlang.org/docs/handbook/declaration-files/do-s-and-don-ts.html)

## 🤝 Contributing Guidelines

### Pull Request Process
1. Create a feature branch from `develop`
2. Make your changes with clear commit messages
3. Write/update tests for your changes
4. Ensure all tests pass
5. Update documentation if needed
6. Submit PR with detailed description
7. Address review comments
8. Squash commits before merge

### Code Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No console.log statements
- [ ] Proper error handling
- [ ] Accessibility considerations
- [ ] Performance implications considered
- [ ] Security implications reviewed

## 📞 Support & Maintenance

### Issue Reporting
- Use GitHub Issues for bug reports
- Include reproduction steps
- Provide browser/environment details
- Attach screenshots if applicable

### Maintenance Schedule
- **Weekly**: Dependency updates review
- **Monthly**: Security audit
- **Quarterly**: Performance review
- **Annually**: Major version upgrades

---

## 🎉 Conclusion

This comprehensive frontend specification provides a complete roadmap for building the AI Legacy Modernization Copilot frontend. The implementation should prioritize:

1. **User Experience**: Intuitive, responsive, and accessible interface
2. **Performance**: Fast load times and smooth interactions
3. **Reliability**: Robust error handling and testing
4. **Maintainability**: Clean code, good documentation, and modular architecture
5. **Security**: Proper authentication, authorization, and data protection

Follow the phased implementation approach, and regularly review progress against the PRD and TRD requirements. The frontend should seamlessly integrate with the backend API to deliver a powerful, user-friendly legacy code modernization platform.

**Next Steps:**
1. Review and approve this specification
2. Set up development environment
3. Begin Phase 1 implementation
4. Schedule regular sprint reviews
5. Iterate based on user feedback

Good luck with the implementation! 🚀
