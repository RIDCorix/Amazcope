/**
 * Suggestion Card Component
 * Displays a single suggestion with quick actions
 */

import {
  AlertTriangle,
  FileEdit,
  Settings,
  Target,
  TrendingUp,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Suggestion } from '@/services/suggestionService';

interface SuggestionCardProps {
  suggestion: Suggestion;
}

const priorityColors = {
  low: 'bg-gray-100 text-gray-800 border-gray-300',
  medium: 'bg-blue-100 text-blue-800 border-blue-300',
  high: 'bg-orange-100 text-orange-800 border-orange-300',
  critical: 'bg-red-100 text-red-800 border-red-300',
};

const priorityIcons = {
  low: Target,
  medium: TrendingUp,
  high: AlertTriangle,
  critical: AlertTriangle,
};

const categoryIcons = {
  pricing: TrendingUp,
  content: FileEdit,
  tracking: Settings,
  competition: Target,
  general: Target,
};

export function SuggestionCard({ suggestion }: SuggestionCardProps) {
  const PriorityIcon = priorityIcons[suggestion.priority] || Target;
  const CategoryIcon =
    categoryIcons[suggestion.category as keyof typeof categoryIcons] || Target;

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 flex-1">
            <CategoryIcon className="h-5 w-5 text-gray-500" />
            <div>
              <CardTitle className="text-lg">{suggestion.title}</CardTitle>
              <CardDescription className="mt-1 line-clamp-2">
                {suggestion.description}
              </CardDescription>
            </div>
          </div>
          <Badge className={priorityColors[suggestion.priority]}>
            <PriorityIcon className="h-3 w-3 mr-1" />
            {suggestion.priority.toUpperCase()}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline">{suggestion.category}</Badge>

          {suggestion.confidence_score && (
            <Badge
              variant="outline"
              className="bg-purple-50 text-purple-700 border-purple-200"
            >
              {Math.round(suggestion.confidence_score * 100)}% confidence
            </Badge>
          )}
        </div>

        <div className="mt-3 text-sm text-gray-500">
          Created {new Date(suggestion.created_at).toLocaleDateString()} at{' '}
          {new Date(suggestion.created_at).toLocaleTimeString()}
        </div>
      </CardContent>
    </Card>
  );
}
