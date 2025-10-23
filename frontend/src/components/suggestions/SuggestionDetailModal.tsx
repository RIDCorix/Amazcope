/**
 * Suggestion Detail Modal
 * Full view of a suggestion with all actions and approval controls
 */

import {
  CheckCircle2,
  Lightbulb,
  TrendingUp,
  XCircle,
  Zap,
} from 'lucide-react';
import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import {
  suggestionService,
  type SuggestionAction,
  type SuggestionDetail,
} from '@/services/suggestionService';

interface SuggestionDetailModalProps {
  suggestionId: string | null;
  open: boolean;
  onClose: () => void;
  onUpdate: () => void;
}

const priorityColors = {
  low: 'bg-gray-100 text-gray-800 border-gray-300',
  medium: 'bg-blue-100 text-blue-800 border-blue-300',
  high: 'bg-orange-100 text-orange-800 border-orange-300',
  critical: 'bg-red-100 text-red-800 border-red-300',
};

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-green-100 text-green-800',
  declined: 'bg-red-100 text-red-800',
  applied: 'bg-blue-100 text-blue-800',
  partially_approved: 'bg-blue-100 text-blue-800',
  expired: 'bg-gray-100 text-gray-800',
  failed: 'bg-red-100 text-red-800',
};

const actionTypeLabels = {
  price_change: 'Price Change',
  content_update: 'Content Update',
  tracking_adjustment: 'Tracking Adjustment',
  metadata_update: 'Metadata Update',
};

export function SuggestionDetailModal({
  suggestionId,
  open,
  onClose,
  onUpdate,
}: SuggestionDetailModalProps) {
  const [suggestion, setSuggestion] = useState<SuggestionDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>(
    {}
  );
  const { toast } = useToast();

  useEffect(() => {
    if (open && suggestionId) {
      fetchSuggestion();
    }
  }, [open, suggestionId]);

  const fetchSuggestion = async () => {
    if (!suggestionId) return;

    setLoading(true);
    try {
      const data = await suggestionService.getSuggestion(suggestionId);
      setSuggestion(data);
    } catch (error: any) {
      toast({
        title: 'Error',
        description:
          error.message || 'Amazcope Lens could not load these insight details',
        variant: 'destructive',
      });
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const handleApproveAll = async () => {
    if (!suggestion) return;

    setLoading(true);
    try {
      await suggestionService.reviewSuggestion(suggestion.id, 'approved');
      toast({
        title: '✨ Approved!',
        description:
          'Amazcope Lens insight has been approved and will be implemented',
      });
      onUpdate();
      onClose();
    } catch (error: any) {
      toast({
        title: 'Error',
        description:
          error.message || 'Amazcope Lens could not approve this insight',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDeclineAll = async () => {
    if (!suggestion) return;

    setLoading(true);
    try {
      await suggestionService.reviewSuggestion(suggestion.id, 'declined');
      toast({
        title: '❌ Declined',
        description: 'Amazcope Lens insight has been declined',
      });
      onUpdate();
      onClose();
    } catch (error: any) {
      toast({
        title: 'Error',
        description:
          error.message || 'Amazcope Lens could not decline this insight',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleActionReview = async (
    actionId: string,
    status: 'approved' | 'declined'
  ) => {
    if (!suggestion) return;

    setActionLoading({ ...actionLoading, [actionId]: true });
    try {
      await suggestionService.reviewActions(suggestion.id, [actionId], status);
      toast({
        title: '✅ Updated',
        description: `Amazcope Lens action has been ${status}`,
      });
      await fetchSuggestion(); // Refresh
    } catch (error: any) {
      toast({
        title: 'Error',
        description:
          error.message || `Amazcope Lens could not ${status} this action`,
        variant: 'destructive',
      });
    } finally {
      setActionLoading({ ...actionLoading, [actionId]: false });
    }
  };

  const handleApplyActions = async (actionIds: string[]) => {
    if (!suggestion) return;

    setLoading(true);
    try {
      const result = await suggestionService.applyActions(
        suggestion.id,
        actionIds
      );
      toast({
        title: '🚀 Applied!',
        description: `Amazcope Lens applied ${result.successful.length} optimization action(s)`,
      });
      if (result.failed.length > 0) {
        toast({
          title: 'Warning',
          description: `${result.failed.length} action(s) failed to apply`,
          variant: 'destructive',
        });
      }
      await fetchSuggestion(); // Refresh
      onUpdate();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to apply actions',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const renderAction = (action: SuggestionAction) => {
    const isLoading = actionLoading[action.id];
    const isPending = action.status === 'pending';
    const isApproved = action.status === 'approved';

    return (
      <div key={action.id} className="border rounded-lg p-4 space-y-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="outline">
                {actionTypeLabels[
                  action.action_type as keyof typeof actionTypeLabels
                ] || action.action_type}
              </Badge>
              <Badge className={statusColors[action.status]}>
                {action.status.toUpperCase()}
              </Badge>
            </div>

            <div className="text-sm font-medium mb-1">
              Field:{' '}
              <span className="text-blue-600">{action.target_field}</span>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-2">
              <div>
                <div className="text-xs text-gray-500 mb-1">Current Value</div>
                <div className="text-sm bg-red-50 border border-red-200 rounded p-2">
                  {action.current_value || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">Proposed Value</div>
                <div className="text-sm bg-green-50 border border-green-200 rounded p-2">
                  {action.proposed_value}
                </div>
              </div>
            </div>

            {action.reasoning && (
              <div className="mt-2 text-sm text-gray-600">
                <Lightbulb className="h-4 w-4 inline mr-1" />
                {action.reasoning}
              </div>
            )}

            {action.estimated_impact && (
              <div className="mt-2 text-sm text-blue-600">
                <TrendingUp className="h-4 w-4 inline mr-1" />
                Expected impact: {action.estimated_impact}
              </div>
            )}

            {action.applied_at && (
              <div className="mt-2 text-xs text-gray-500">
                Applied: {new Date(action.applied_at).toLocaleString()}
              </div>
            )}
          </div>
        </div>

        {isPending && (
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="default"
              onClick={() => handleActionReview(action.id, 'approved')}
              disabled={isLoading}
              className="flex-1"
            >
              <CheckCircle2 className="h-4 w-4 mr-1" />
              Approve
            </Button>
            <Button
              size="sm"
              variant="destructive"
              onClick={() => handleActionReview(action.id, 'declined')}
              disabled={isLoading}
              className="flex-1"
            >
              <XCircle className="h-4 w-4 mr-1" />
              Decline
            </Button>
          </div>
        )}

        {isApproved && !action.applied_at && (
          <Button
            size="sm"
            variant="default"
            onClick={() => handleApplyActions([action.id])}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700"
          >
            <Zap className="h-4 w-4 mr-1" />
            Apply Now
          </Button>
        )}
      </div>
    );
  };

  if (!open) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>Suggestion Details</DialogTitle>
          <DialogDescription>
            Review and manage intelligent recommendations from Amazcope Lens
          </DialogDescription>
        </DialogHeader>

        {loading && !suggestion ? (
          <div className="space-y-4">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        ) : suggestion ? (
          <ScrollArea className="max-h-[60vh]">
            <div className="space-y-4 pr-4">
              {/* Header Info */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Badge className={priorityColors[suggestion.priority]}>
                    {suggestion.priority.toUpperCase()}
                  </Badge>
                  <Badge className={statusColors[suggestion.status]}>
                    {suggestion.status.replace('_', ' ').toUpperCase()}
                  </Badge>
                  <Badge variant="outline">{suggestion.category}</Badge>
                </div>

                <h3 className="text-xl font-semibold">{suggestion.title}</h3>
                <p className="text-gray-600">{suggestion.description}</p>

                {suggestion.reasoning && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-2">
                    <div className="flex items-start gap-2">
                      <Lightbulb className="h-5 w-5 text-blue-600 mt-0.5" />
                      <div>
                        <div className="font-medium text-blue-900 mb-1">
                          AI Reasoning
                        </div>
                        <div className="text-sm text-blue-800">
                          {suggestion.reasoning}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {suggestion.estimated_impact &&
                  typeof suggestion.estimated_impact === 'string' && (
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                      <div className="flex items-start gap-2">
                        <TrendingUp className="h-5 w-5 text-purple-600 mt-0.5" />
                        <div>
                          <div className="font-medium text-purple-900 mb-1">
                            Expected Impact
                          </div>
                          <div className="text-sm text-purple-800">
                            {suggestion.estimated_impact}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
              </div>

              <Separator />

              {/* Actions */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold">
                    Actions ({suggestion.actions.length})
                  </h4>

                  {suggestion.approved_action_count > 0 && !loading && (
                    <Button
                      size="sm"
                      variant="default"
                      onClick={() =>
                        handleApplyActions(
                          suggestion.actions
                            .filter(
                              a => a.status === 'approved' && !a.applied_at
                            )
                            .map(a => a.id)
                        )
                      }
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <Zap className="h-4 w-4 mr-1" />
                      Apply All Approved
                    </Button>
                  )}
                </div>

                <div className="space-y-3">
                  {suggestion.actions.map(renderAction)}
                </div>
              </div>

              {/* Metadata */}
              <Separator />
              <div className="text-sm text-gray-500 space-y-1">
                <div>
                  Created: {new Date(suggestion.created_at).toLocaleString()}
                </div>
                {suggestion.reviewed_at && (
                  <div>
                    Reviewed:{' '}
                    {new Date(suggestion.reviewed_at).toLocaleString()}
                  </div>
                )}
                {suggestion.confidence_score && (
                  <div>
                    AI Confidence:{' '}
                    {Math.round(suggestion.confidence_score * 100)}%
                  </div>
                )}
              </div>
            </div>
          </ScrollArea>
        ) : null}

        <DialogFooter>
          {suggestion?.status === 'pending' && (
            <>
              <Button variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleDeclineAll}
                disabled={loading}
              >
                <XCircle className="h-4 w-4 mr-2" />
                Decline All
              </Button>
              <Button onClick={handleApproveAll} disabled={loading}>
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Approve All
              </Button>
            </>
          )}
          {suggestion?.status !== 'pending' && (
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
