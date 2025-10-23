/**
 * Enums that mirror backend Django model choices
 * These should be kept in sync with backend/src/core/enums.py
 */

/**
 * Star type - represents the kind/content of a star node
 * Mirrors backend: core.enums.StarType
 */
export enum StarType {
  READING = 'reading',
  VOCABULARY = 'vocabulary',
  CODING = 'coding',
}

/**
 * Completion type - represents how a node's completion is evaluated
 * Mirrors backend: core.enums.CompletionType
 */
export enum CompletionType {
  READING = 'reading',
  USER_CHECK = 'user_check',
  PULL_REQUESTS = 'pull_requests',
  EXTERNAL_VERIFY = 'external_verify',
}

/**
 * Type guard to check if a string is a valid CompletionType
 */
export function isCompletionType(value: string): value is CompletionType {
  return Object.values(CompletionType).includes(value as CompletionType);
}

/**
 * Type guard to check if a string is a valid StarType
 */
export function isStarType(value: string): value is StarType {
  return Object.values(StarType).includes(value as StarType);
}

/**
 * Get display label for CompletionType
 */
export function getCompletionTypeLabel(type: CompletionType): string {
  switch (type) {
    case CompletionType.READING:
      return 'Reading';
    case CompletionType.USER_CHECK:
      return 'User Check';
    case CompletionType.PULL_REQUESTS:
      return 'Pull Requests';
    case CompletionType.EXTERNAL_VERIFY:
      return 'External Verify';
    default:
      return type;
  }
}

/**
 * Get display label for StarType
 */
export function getStarTypeLabel(type: StarType): string {
  switch (type) {
    case StarType.READING:
      return 'Reading';
    case StarType.VOCABULARY:
      return 'Vocabulary';
    case StarType.CODING:
      return 'Coding';
    default:
      return type;
  }
}
