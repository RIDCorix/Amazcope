import { format, formatDistanceToNow } from 'date-fns';
import {
  AlertCircle,
  BarChart3,
  Calendar,
  DollarSign,
  ExternalLink,
  Eye,
  FileText,
  Package,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import { Notification } from '@/services/notificationService';

interface DailyReportNotificationProps {
  notification: Notification;
  onMarkAsRead?: (id: string) => void;
  className?: string;
}

interface ReportData {
  summary: {
    products_analyzed: number;
    total_insights: number;
    priority_alerts: number;
    potential_savings: number;
  };
  highlights: Array<{
    type: 'price_drop' | 'bsr_improvement' | 'new_competitor' | 'opportunity';
    title: string;
    description: string;
    impact: 'high' | 'medium' | 'low';
    value?: string;
    product_asin?: string;
  }>;
  insights: Array<{
    category: string;
    message: string;
    action_required: boolean;
    confidence: number;
  }>;
  recommendations: Array<{
    title: string;
    description: string;
    priority: 'urgent' | 'high' | 'medium' | 'low';
    estimated_impact: string;
  }>;
}

// Parse report data from notification message (assuming it's JSON or structured)
const parseReportData = (message: string): ReportData | null => {
  try {
    // Check if message contains JSON data
    if (message.includes('{')) {
      const jsonStart = message.indexOf('{');
      const jsonStr = message.substring(jsonStart);
      return JSON.parse(jsonStr);
    }

    // Fallback: parse from structured text (mock data for demo)
    return {
      summary: {
        products_analyzed: 12,
        total_insights: 8,
        priority_alerts: 3,
        potential_savings: 1240,
      },
      highlights: [
        {
          type: 'price_drop',
          title: 'Competitor Price Drop Detected',
          description:
            'Main competitor reduced price by 15% on similar product',
          impact: 'high',
          value: '$23.99 → $20.39',
          product_asin: 'B07XJ8C8F5',
        },
        {
          type: 'bsr_improvement',
          title: 'BSR Ranking Improved',
          description: 'Your product moved up 23 positions in category ranking',
          impact: 'medium',
          value: '#145 → #122',
        },
        {
          type: 'opportunity',
          title: 'Keyword Opportunity',
          description: 'New high-volume keyword detected with low competition',
          impact: 'high',
          value: '2.3K searches/month',
        },
      ],
      insights: [
        {
          category: 'Pricing Strategy',
          message:
            'Consider adjusting prices based on competitor movements to maintain competitive edge.',
          action_required: true,
          confidence: 0.85,
        },
        {
          category: 'Inventory Management',
          message: 'Stock levels are optimal for current demand patterns.',
          action_required: false,
          confidence: 0.92,
        },
      ],
      recommendations: [
        {
          title: 'Update Product Pricing',
          description:
            'Adjust pricing on 3 products to match competitive landscape while maintaining margins',
          priority: 'high',
          estimated_impact: '+$450/month revenue',
        },
        {
          title: 'Optimize Listing Keywords',
          description:
            'Add identified high-value keywords to product listings for better discoverability',
          priority: 'medium',
          estimated_impact: '+15% organic traffic',
        },
      ],
    };
  } catch (error) {
    console.error('Failed to parse report data:', error);
    return null;
  }
};

const highlightIcons = {
  price_drop: TrendingDown,
  bsr_improvement: TrendingUp,
  new_competitor: AlertCircle,
  opportunity: Sparkles,
};

const highlightColors = {
  price_drop: 'text-red-600 bg-red-100',
  bsr_improvement: 'text-green-600 bg-green-100',
  new_competitor: 'text-orange-600 bg-orange-100',
  opportunity: 'text-blue-600 bg-blue-100',
};

const impactColors = {
  high: 'bg-red-100 text-red-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-green-100 text-green-800',
};

const priorityColors = {
  urgent: 'bg-red-100 text-red-800',
  high: 'bg-orange-100 text-orange-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-green-100 text-green-800',
};

export function DailyReportNotification({
  notification,
  onMarkAsRead,
  className,
}: DailyReportNotificationProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('summary');

  const reportData = parseReportData(notification.message);
  const isUnread = notification.status === 'unread';

  const handleMarkAsRead = () => {
    if (onMarkAsRead && isUnread) {
      onMarkAsRead(notification.id);
    }
  };

  const handleViewReport = () => {
    setIsOpen(true);
    if (isUnread) {
      handleMarkAsRead();
    }
  };

  const formatTimeAgo = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch {
      return 'Unknown time';
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMMM d, yyyy');
    } catch {
      return 'Unknown date';
    }
  };

  if (!reportData) {
    // Fallback to regular notification display if parsing fails
    return (
      <Card className={cn('border-l-4 border-l-blue-500', className)}>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-blue-600" />
              <CardTitle className="text-base">{notification.title}</CardTitle>
              {isUnread && (
                <Badge
                  variant="secondary"
                  className="bg-blue-100 text-blue-800"
                >
                  New
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600 mb-3">{notification.message}</p>
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>{formatTimeAgo(notification.created_at)}</span>
            <Button size="sm" onClick={handleMarkAsRead}>
              View Report
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card
        className={cn(
          'border-l-4 border-l-blue-500 transition-all duration-200 hover:shadow-md cursor-pointer',
          isUnread ? 'bg-blue-50/50' : 'bg-white',
          className
        )}
      >
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-blue-100 rounded-full">
                <BarChart3 className="h-4 w-4 text-blue-600" />
              </div>
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  Daily Market Report
                  {isUnread && (
                    <Badge
                      variant="secondary"
                      className="bg-blue-100 text-blue-800"
                    >
                      New
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription className="text-xs">
                  {formatDate(notification.created_at)} • Generated by AI
                </CardDescription>
              </div>
            </div>

            <Dialog open={isOpen} onOpenChange={setIsOpen}>
              <DialogTrigger asChild>
                <Button size="sm" onClick={handleViewReport}>
                  <Eye className="mr-1 h-3 w-3" />
                  View Report
                </Button>
              </DialogTrigger>
            </Dialog>
          </div>
        </CardHeader>

        <CardContent>
          {/* Quick Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            <div className="text-center">
              <div className="text-lg font-semibold text-gray-900">
                {reportData.summary.products_analyzed}
              </div>
              <div className="text-xs text-gray-500">Products Analyzed</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-blue-600">
                {reportData.summary.total_insights}
              </div>
              <div className="text-xs text-gray-500">Insights</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-orange-600">
                {reportData.summary.priority_alerts}
              </div>
              <div className="text-xs text-gray-500">Alerts</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-green-600">
                ${reportData.summary.potential_savings}
              </div>
              <div className="text-xs text-gray-500">Savings</div>
            </div>
          </div>

          {/* Top Highlights Preview */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700">
              Key Highlights
            </h4>
            {reportData.highlights.slice(0, 2).map((highlight, index) => {
              const Icon = highlightIcons[highlight.type];
              return (
                <div
                  key={index}
                  className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg"
                >
                  <div
                    className={cn(
                      'p-1 rounded-full',
                      highlightColors[highlight.type]
                    )}
                  >
                    <Icon className="h-3 w-3" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {highlight.title}
                    </p>
                    <p className="text-xs text-gray-600 truncate">
                      {highlight.description}
                    </p>
                  </div>
                  <Badge
                    variant="secondary"
                    className={cn('text-xs', impactColors[highlight.impact])}
                  >
                    {highlight.impact}
                  </Badge>
                </div>
              );
            })}
            {reportData.highlights.length > 2 && (
              <p className="text-xs text-gray-500 text-center">
                +{reportData.highlights.length - 2} more insights in full report
              </p>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between pt-3 mt-3 border-t">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Calendar className="h-3 w-3" />
              <span>{formatTimeAgo(notification.created_at)}</span>
            </div>
            <Button size="sm" variant="ghost" onClick={() => setIsOpen(true)}>
              View Full Report
              <ExternalLink className="ml-1 h-3 w-3" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Full Report Modal */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Daily Market Report - {formatDate(notification.created_at)}
            </DialogTitle>
            <DialogDescription>
              AI-generated insights and recommendations for your Amazon products
            </DialogDescription>
          </DialogHeader>

          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            className="w-full"
          >
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="summary">Summary</TabsTrigger>
              <TabsTrigger value="highlights">Highlights</TabsTrigger>
              <TabsTrigger value="insights">Insights</TabsTrigger>
              <TabsTrigger value="recommendations">Actions</TabsTrigger>
            </TabsList>

            <TabsContent value="summary" className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  {
                    label: 'Products Analyzed',
                    value: reportData.summary.products_analyzed,
                    icon: Package,
                  },
                  {
                    label: 'Total Insights',
                    value: reportData.summary.total_insights,
                    icon: Sparkles,
                  },
                  {
                    label: 'Priority Alerts',
                    value: reportData.summary.priority_alerts,
                    icon: AlertCircle,
                  },
                  {
                    label: 'Potential Savings',
                    value: `$${reportData.summary.potential_savings}`,
                    icon: DollarSign,
                  },
                ].map(stat => {
                  const Icon = stat.icon;
                  return (
                    <Card key={stat.label}>
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">
                          {stat.label}
                        </CardTitle>
                        <Icon className="h-4 w-4 text-muted-foreground" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{stat.value}</div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </TabsContent>

            <TabsContent value="highlights" className="space-y-4">
              {reportData.highlights.map((highlight, index) => {
                const Icon = highlightIcons[highlight.type];
                return (
                  <Card key={index}>
                    <CardHeader>
                      <div className="flex items-center gap-3">
                        <div
                          className={cn(
                            'p-2 rounded-full',
                            highlightColors[highlight.type]
                          )}
                        >
                          <Icon className="h-4 w-4" />
                        </div>
                        <div className="flex-1">
                          <CardTitle className="text-base">
                            {highlight.title}
                          </CardTitle>
                          <CardDescription>
                            {highlight.description}
                          </CardDescription>
                        </div>
                        <Badge className={cn(impactColors[highlight.impact])}>
                          {highlight.impact} impact
                        </Badge>
                      </div>
                    </CardHeader>
                    {(highlight.value || highlight.product_asin) && (
                      <CardContent>
                        <div className="flex items-center gap-4">
                          {highlight.value && (
                            <div>
                              <span className="text-sm text-gray-600">
                                Value:{' '}
                              </span>
                              <span className="font-medium">
                                {highlight.value}
                              </span>
                            </div>
                          )}
                          {highlight.product_asin && (
                            <div>
                              <span className="text-sm text-gray-600">
                                ASIN:{' '}
                              </span>
                              <span className="font-mono text-sm">
                                {highlight.product_asin}
                              </span>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    )}
                  </Card>
                );
              })}
            </TabsContent>

            <TabsContent value="insights" className="space-y-4">
              {reportData.insights.map((insight, index) => (
                <Card key={index}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-base">
                          {insight.category}
                        </CardTitle>
                        <CardDescription>{insight.message}</CardDescription>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={
                            insight.action_required
                              ? 'destructive'
                              : 'secondary'
                          }
                        >
                          {insight.action_required ? 'Action Required' : 'Info'}
                        </Badge>
                        <Badge variant="outline">
                          {Math.round(insight.confidence * 100)}% confident
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                </Card>
              ))}
            </TabsContent>

            <TabsContent value="recommendations" className="space-y-4">
              {reportData.recommendations.map((rec, index) => (
                <Card key={index}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-base">{rec.title}</CardTitle>
                        <CardDescription className="mt-1">
                          {rec.description}
                        </CardDescription>
                      </div>
                      <div className="flex flex-col gap-2 items-end">
                        <Badge className={cn(priorityColors[rec.priority])}>
                          {rec.priority} priority
                        </Badge>
                        <span className="text-sm font-medium text-green-600">
                          {rec.estimated_impact}
                        </span>
                      </div>
                    </div>
                  </CardHeader>
                </Card>
              ))}
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>
    </>
  );
}
