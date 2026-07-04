/**
 * Typed API client for the LMS backend.
 * All requests go through /api proxy defined in vite.config.ts.
 *
 * TODO: Replace handwritten endpoint helpers with auto-generated typed client
 * once `openapi-typescript` / `openapi-fetch` codegen is wired up from the
 * FastAPI OpenAPI spec.  Keep only the base `request()` helper and shared
 * auth/config here.
 */

const BASE_URL = '/api'

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const { headers: optionHeaders, ...restOptions } = options
  const res = await fetch(`${BASE_URL}${path}`, {
    ...restOptions,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(optionHeaders ?? {}),
    },
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error((error as { detail: string }).detail ?? res.statusText)
  }

  return res.json() as Promise<T>
}

// ---- Health ----------------------------------------------------------------

export interface HealthResponse {
  status: string
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

// ---- Users -----------------------------------------------------------------

export interface UserPublic {
  id: string
  email: string
  full_name: string
  role: 'student' | 'instructor' | 'admin'
  is_active: boolean
}

export interface UserCreate {
  email: string
  full_name: string
  password: string
  role?: 'student' | 'instructor' | 'admin'
}

export function createUser(data: UserCreate): Promise<UserPublic> {
  return request<UserPublic>('/users/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function getUser(userId: string): Promise<UserPublic> {
  return request<UserPublic>(`/users/${userId}`)
}

// ---- Courses ---------------------------------------------------------------

export interface CoursePublic {
  id: string
  title: string
  description: string
  instructor_id: string
  is_published: boolean
}

export interface CourseCreate {
  title: string
  description: string
}

export function listCourses(): Promise<CoursePublic[]> {
  return request<CoursePublic[]>('/courses/')
}

export function createCourse(data: CourseCreate): Promise<CoursePublic> {
  return request<CoursePublic>('/courses/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function getCourse(courseId: string): Promise<CoursePublic> {
  return request<CoursePublic>(`/courses/${courseId}`)
}

// ---- Modules ---------------------------------------------------------------

export interface ModulePublic {
  id: string
  course_id: string
  title: string
  order_index: number
  content_md: string
}

export function listModules(courseId: string): Promise<ModulePublic[]> {
  return request<ModulePublic[]>(`/courses/${courseId}/modules`)
}

// ---- Assignments -----------------------------------------------------------

export type GradingType = 'deterministic' | 'llm_rubric' | 'hybrid'

export interface AssignmentPublic {
  id: string
  module_id: string
  title: string
  description_md: string
  grading_type: GradingType
  max_score: number
  due_at: string | null
}

export function listAssignments(moduleId: string): Promise<AssignmentPublic[]> {
  return request<AssignmentPublic[]>(
    `/assignments/?module_id=${encodeURIComponent(moduleId)}`,
  )
}

// ---- Submissions -----------------------------------------------------------

export interface SubmissionPublic {
  id: string
  assignment_id: string
  student_id: string
  content: string
  status: 'pending' | 'grading' | 'graded' | 'error'
  created_at: string
}

export interface SubmissionCreate {
  assignment_id: string
  content: string
}

export function createSubmission(
  data: SubmissionCreate,
): Promise<SubmissionPublic> {
  return request<SubmissionPublic>('/submissions/', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function getSubmission(submissionId: string): Promise<SubmissionPublic> {
  return request<SubmissionPublic>(`/submissions/${submissionId}`)
}
