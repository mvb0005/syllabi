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
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
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
  created_at: string
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
  created_at: string
}

export interface CourseCreate {
  title: string
  description: string
  instructor_id: string
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
  student_id: string
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
