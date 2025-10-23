export interface Title {
  id: string;
  name: string;
  description: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  category: 'achievement' | 'streak' | 'skill' | 'special' | 'seasonal';
  icon?: string;
  color?: string;
  requirements: TitleRequirement[];
  isHidden?: boolean; // Hidden until unlocked
  unlockedAt?: Date;
  isEquipped?: boolean;
}

export interface TitleRequirement {
  type:
    | 'problems_solved'
    | 'streak_days'
    | 'stars_earned'
    | 'skills_mastered'
    | 'time_spent'
    | 'perfect_scores'
    | 'achievements_unlocked';
  value: number;
  description: string;
}

export interface UserTitle {
  id: string;
  userId: string;
  titleId: string;
  title: Title;
  unlockedAt: Date;
  isEquipped: boolean;
  progress?: number; // For titles that can be progressed towards
}

export interface TitleProgress {
  titleId: string;
  currentProgress: number;
  requirement: TitleRequirement;
  isUnlocked: boolean;
  progressPercentage: number;
}

export const TITLE_RARITIES = {
  common: {
    color: 'text-gray-600',
    bgColor: 'bg-gray-500/10',
    borderColor: 'border-gray-300',
    name: 'Common',
  },
  rare: {
    color: 'text-blue-600',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-300',
    name: 'Rare',
  },
  epic: {
    color: 'text-purple-600',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-300',
    name: 'Epic',
  },
  legendary: {
    color: 'text-orange-600',
    bgColor: 'bg-orange-500/10',
    borderColor: 'border-orange-300',
    name: 'Legendary',
  },
} as const;

export const TITLE_CATEGORIES = {
  achievement: { name: 'Achievement', icon: '🏆' },
  streak: { name: 'Streak', icon: '🔥' },
  skill: { name: 'Skill', icon: '⚡' },
  special: { name: 'Special', icon: '⭐' },
  seasonal: { name: 'Seasonal', icon: '🎃' },
} as const;
