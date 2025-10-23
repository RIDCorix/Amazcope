'use client';

import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  RefreshCcw,
  Sparkles,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { SuggestionCard } from '@/components/suggestions/SuggestionCard';
import { SuggestionDetailModal } from '@/components/suggestions/SuggestionDetailModal';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { ThemedSelect } from '@/components/ui/themed-select';
import { useToast } from '@/hooks/use-toast';
import {
  suggestionService,
  type Suggestion,
  type SuggestionStats,
} from '@/services/suggestionService';

type FilterStatus =
  | 'all'
  | 'pending'
  | 'approved'
  | 'declined'
  | 'partially_approved'
  | 'expired';
type FilterPriority = 'all' | 'low' | 'medium' | 'high' | 'critical';

const priorityOptions = [
  { value: 'all', label: 'All Priorities' },
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
];

const statusOptions = [
  { value: 'all', label: 'All Statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'declined', label: 'Declined' },
  { value: 'partially_approved', label: 'Partially Approved' },
  { value: 'expired', label: 'Expired' },
];

export default function SuggestionsPage() {
  const navigate = useNavigate();
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [stats, setStats] = useState<SuggestionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedSuggestionId, setSelectedSuggestionId] = useState<
    string | null
  >(null);
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');
  const [filterPriority, setFilterPriority] = useState<FilterPriority>('all');
  const { toast } = useToast();

  useEffect(() => {
    fetchData();
  }, [navigate, filterStatus, filterPriority]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [suggestionsData, statsData] = await Promise.all([
        suggestionService.listSuggestions({
          status_filter: filterStatus === 'all' ? undefined : filterStatus,
          priority: filterPriority === 'all' ? undefined : filterPriority,
        }),
        suggestionService.getStats(),
      ]);
      setSuggestions(suggestionsData);
      setStats(statsData);
    } catch (error: any) {
      toast({
        title: 'Error',
        description:
          error.message ||
          'Amazcope Lens could not retrieve insights right now',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Sparkles className="h-8 w-8 text-purple-600" />
            Amazcope Lens Insights
          </h1>
          <p className="text-gray-500 mt-1">
            Smart optimization insights powered by your personal Amazon
            analytics AI
          </p>
        </div>
        <Button onClick={fetchData} variant="outline" disabled={loading}>
          <RefreshCcw
            className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`}
          />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-500">
                Total Suggestions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-purple-600" />
                <div className="text-2xl font-bold">
                  {stats.total_suggestions}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-500">
                Pending Review
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-yellow-600" />
                <div className="text-2xl font-bold">{stats.pending || 0}</div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-500">
                Approved
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <div className="text-2xl font-bold">{stats.approved || 0}</div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-500">
                Critical Priority
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                <div className="text-2xl font-bold">
                  {stats.by_priority.critical || 0}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>
            Filter suggestions by status and priority
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Status</label>
              <ThemedSelect
                value={statusOptions.find(opt => opt.value === filterStatus)}
                onChange={(option: any) =>
                  setFilterStatus((option?.value || 'all') as FilterStatus)
                }
                options={statusOptions}
                placeholder="Select status..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Priority</label>
              <ThemedSelect
                value={priorityOptions.find(
                  opt => opt.value === filterPriority
                )}
                onChange={(option: any) =>
                  setFilterPriority((option?.value || 'all') as FilterPriority)
                }
                options={priorityOptions}
                placeholder="Select priority..."
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Suggestions Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">
            Suggestions ({suggestions.length})
          </h2>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-6 w-3/4" />
                  <Skeleton className="h-4 w-full mt-2" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-20 w-full" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : suggestions.length === 0 ? (
          <Card>
            <CardContent className="py-12">
              <div className="text-center">
                <Sparkles className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  No suggestions found
                </h3>
                <p className="text-gray-500">
                  {filterStatus !== 'all' || filterPriority !== 'all'
                    ? 'Try adjusting your filters'
                    : 'Amazcope Lens is analyzing your products... insights will appear here soon!'}
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {suggestions.map(suggestion => (
              <SuggestionCard key={suggestion.id} suggestion={suggestion} />
            ))}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      <SuggestionDetailModal
        suggestionId={selectedSuggestionId}
        open={selectedSuggestionId !== null}
        onClose={() => setSelectedSuggestionId(null)}
        onUpdate={fetchData}
      />
    </div>
  );
}
