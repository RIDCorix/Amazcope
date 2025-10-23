/**
 * amazcope API TypeScript Types
 *
 * Auto-generated from OpenAPI schema
 * Do not edit manually
 */

// Base Types
export interface ApiResponse<T = object> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T = object> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ErrorResponse {
  error: string;
  code?: string;
  details?: Record<string, string[]>;
  timestamp?: string;
}

// Authentication Types
export interface TokenPair {
  access: string;
  refresh: string;
}

export interface TokenRefresh {
  refresh: string;
  access: string;
}

export interface TokenVerify {
  token: string;
}

export interface TokenBlacklist {
  refresh: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
}

export interface AuthResponse {
  token: string;
  refreshToken: string;
  user: UserDetail;
}

// Authentication Request Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

// User Types
export interface UserDetail {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserProfile {
  id: string;
  user: UserDetail;
  learningGoals?: string;
  skillLevel: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  teachingExperience?: number;
  expertiseAreas: Record<string, object>;
  certifications: Record<string, object>;
  timezone: string;
  lastActive?: string;
  totalLearningTime: string;
  // Inventory slot limits (category-specific)
  materialSlots: number;
  toolSlots: number;
  consumableSlots: number;
  equipmentSlots: number;
  learningSlots: number;
  createdAt: string;
  updatedAt: string;
}

export interface UserSettings {
  id: string;
  emailNotifications: boolean;
  pushNotifications: boolean;
  courseReminders: boolean;
  achievementNotifications: boolean;
  weeklyProgressEmails: boolean;
  publicProfile: boolean;
  showProgressPublicly: boolean;
  allowMessages: boolean;
  dailyGoalMinutes: number;
  preferredDifficulty: 'beginner' | 'intermediate' | 'advanced' | 'mixed';
  autoContinueCourses: boolean;
  theme: 'light' | 'dark' | 'system';
  language: string;
  reducedMotion: boolean;
  contentCategories: Record<string, object>;
  blockedTags: Record<string, object>;
}

// Skill Tree Types
export interface SkillTree {
  id: string;
  title: string;
  slug: string;
  description: string;
  shortDescription: string;
  status: 'draft' | 'published' | 'archived';
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  estimatedDuration?: string;
  thumbnail?: ImageModel;
  thumbnail_id?: string;
  category: string;
  tags: Record<string, object>;
  viewCount: number;
  enrollmentCount: number;
  completionCount: number;
  isPublic: boolean;
  isFree: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface SkillTreeCreate {
  title: string;
  slug: string;
  description: string;
  shortDescription: string;
  category: string;
  difficulty?: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  estimatedDuration?: string;
  thumbnail?: File;
  tags?: Record<string, object>;
  isPublic?: boolean;
  isFree?: boolean;
}

// Course Types
export interface Course {
  id: string;
  title: string;
  slug: string;
  description: string;
  content: Record<string, object>;
  courseType:
    | 'text'
    | 'video'
    | 'interactive'
    | 'quiz'
    | 'project'
    | 'exercise';
  estimatedDuration?: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  order: number;
  status: 'draft' | 'published' | 'archived';
  positionX: number;
  positionY: number;
  videoUrl?: string;
  resources: Record<string, object>;
  createdAt: string;
  updatedAt: string;
}

export interface CourseCreate {
  title: string;
  slug: string;
  description: string;
  content?: Record<string, object>;
  courseType:
    | 'text'
    | 'video'
    | 'interactive'
    | 'quiz'
    | 'project'
    | 'exercise';
  estimatedDuration?: string;
  difficulty?: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  order: number;
  positionX?: number;
  positionY?: number;
  videoUrl?: string;
  resources?: Record<string, object>;
}

export interface CourseResponse {
  results: Course[];
  count: number;
  next?: string;
  previous?: string;
}

export interface CreateCourseRequest {
  title: string;
  description?: string;
  content: string;
  skillTreeId: string;
  order: number;
  prerequisites?: string[];
}

// Quiz Types
export interface Quiz {
  id: string;
  title: string;
  description?: string;
  timeLimit?: string;
  passingScore: number;
  maxAttempts: number;
  questions: QuizQuestion[];
}

export interface QuizQuestion {
  id: string;
  questionText: string;
  questionType:
    | 'multiple_choice'
    | 'true_false'
    | 'short_answer'
    | 'essay'
    | 'fill_blank';
  choices: Record<string, object>;
  correctAnswers: Record<string, object>;
  explanation?: string;
  points: number;
}

export interface QuizCreate {
  title: string;
  description?: string;
  timeLimit?: string;
  passingScore?: number;
  maxAttempts?: number;
}

export interface QuizQuestionCreate {
  questionText: string;
  questionType:
    | 'multiple_choice'
    | 'true_false'
    | 'short_answer'
    | 'essay'
    | 'fill_blank';
  choices?: Record<string, object>;
  correctAnswers: Record<string, object>;
  explanation?: string;
  points?: number;
}

// Progress Types
export interface CourseProgress {
  id: string;
  user: string;
  course: string;
  status: 'not_started' | 'in_progress' | 'completed';
  progress_percentage: number;
  time_spent: number;
  score?: number;
  started_at?: string;
  completed_at?: string;
  last_accessed_at: string;
}

export interface SkillTreeEnrollment {
  id: string;
  user: string;
  skill_tree: string;
  enrolled_at: string;
  progress_percentage: number;
  is_completed: boolean;
  completed_at?: string;
  last_accessed_at: string;
}

// Achievement Types
export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  points: number;
  criteria: Record<string, object>;
}

export interface UserAchievement {
  id: string;
  user: string;
  achievement: Achievement;
  earned_at: string;
  progress: number;
}

// Filter Types
export interface SkillTreeFilters {
  search?: string;
  difficulty?: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  category?: string;
  isFree?: boolean;
  status?: 'draft' | 'published' | 'archived';
  ordering?: string;
  page?: number;
}

export interface CourseFilters {
  search?: string;
  courseType?:
    | 'text'
    | 'video'
    | 'interactive'
    | 'quiz'
    | 'project'
    | 'exercise';
  difficulty?: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  status?: 'draft' | 'published' | 'archived';
  ordering?: string;
  page?: number;
}

export interface QuizFilters {
  search?: string;
  ordering?: string;
  page?: number;
}

// Notification Types
export interface Notification {
  id: string;
  user: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  isRead: boolean;
  createdAt: string;
  actionUrl?: string;
}

// System Types
export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  version: string;
  database: boolean;
  cache: boolean;
}

export interface SystemConfig {
  app_name: string;
  version: string;
  environment: string;
  features: Record<string, boolean>;
  limits: Record<string, number>;
}

// API Client Configuration
export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
  withCredentials?: boolean;
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  headers?: Record<string, string>;
  params?: Record<string, object>;
  data?: object;
  timeout?: number;
}

// Image Model Types
export interface ImageModel {
  id: string;
  title: string;
  altText: string;
  description?: string;
  imageType:
    | 'avatar'
    | 'skill_tree_thumbnail'
    | 'course_image'
    | 'achievement_icon'
    | 'general';
  url: string;
  thumbnailUrl: string;
  width?: number;
  height?: number;
  fileSize?: number;
  fileFormat?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}
