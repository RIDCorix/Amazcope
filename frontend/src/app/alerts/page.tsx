import { AlertCircle, Bell, Package, TrendingDown } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

interface Alert {
  id: number;
  product: {
    id: number;
    asin: string;
    title: string;
  };
  alert_type: string;
  threshold: number;
  current_value: number;
  triggered_at: string;
  is_resolved: boolean;
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch('http://localhost:8000/api/v1/alerts', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAlerts(data.alerts || []);
      }
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const resolveAlert = async (alertId: number) => {
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(
        `http://localhost:8000/api/v1/alerts/${alertId}/resolve`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        fetchAlerts();
      }
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'price_drop':
        return <TrendingDown className="h-5 w-5 text-green-600" />;
      case 'price_increase':
        return <TrendingDown className="h-5 w-5 text-red-600 rotate-180" />;
      case 'out_of_stock':
        return <Package className="h-5 w-5 text-orange-600" />;
      default:
        return <AlertCircle className="h-5 w-5 text-blue-600" />;
    }
  };

  const getAlertBadge = (type: string) => {
    switch (type) {
      case 'price_drop':
        return (
          <Badge variant="default" className="bg-green-600">
            Price Drop
          </Badge>
        );
      case 'price_increase':
        return <Badge variant="destructive">Price Increase</Badge>;
      case 'out_of_stock':
        return (
          <Badge variant="secondary" className="bg-orange-600 text-white">
            Out of Stock
          </Badge>
        );
      default:
        return <Badge variant="outline">{type}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading alerts...</div>
        </div>
      </div>
    );
  }

  const activeAlerts = alerts.filter(alert => !alert.is_resolved);
  const resolvedAlerts = alerts.filter(alert => alert.is_resolved);

  return (
    <div className="container mx-auto p-6">
      <div className="flex items-center gap-3 mb-6">
        <Bell className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold">Alerts</h1>
          <p className="text-gray-600">
            Manage your product price and stock alerts
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Active Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">
              {activeAlerts.length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Resolved
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {resolvedAlerts.length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{alerts.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Active Alerts */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Active Alerts</CardTitle>
          <CardDescription>Alerts that require your attention</CardDescription>
        </CardHeader>
        <CardContent>
          {activeAlerts.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No active alerts
            </div>
          ) : (
            <div className="space-y-4">
              {activeAlerts.map(alert => (
                <div
                  key={alert.id}
                  className="flex items-start gap-4 p-4 border rounded-lg"
                >
                  <div className="mt-1">{getAlertIcon(alert.alert_type)}</div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      {getAlertBadge(alert.alert_type)}
                      <span className="text-sm text-gray-500">
                        {new Date(alert.triggered_at).toLocaleString()}
                      </span>
                    </div>
                    <h3 className="font-semibold mb-1">
                      {alert.product.title}
                    </h3>
                    <p className="text-sm text-gray-600">
                      ASIN: {alert.product.asin}
                    </p>
                    <div className="mt-2 text-sm">
                      <span className="text-gray-600">Current: </span>
                      <span className="font-semibold">
                        ${alert.current_value}
                      </span>
                      <span className="text-gray-600 ml-4">Threshold: </span>
                      <span className="font-semibold">${alert.threshold}</span>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => resolveAlert(alert.id)}
                  >
                    Resolve
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Resolved Alerts */}
      {resolvedAlerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Resolved Alerts</CardTitle>
            <CardDescription>Previously resolved alerts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {resolvedAlerts.map(alert => (
                <div
                  key={alert.id}
                  className="flex items-start gap-4 p-4 border rounded-lg opacity-60"
                >
                  <div className="mt-1">{getAlertIcon(alert.alert_type)}</div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      {getAlertBadge(alert.alert_type)}
                      <Badge variant="outline" className="bg-gray-100">
                        Resolved
                      </Badge>
                      <span className="text-sm text-gray-500">
                        {new Date(alert.triggered_at).toLocaleString()}
                      </span>
                    </div>
                    <h3 className="font-semibold mb-1">
                      {alert.product.title}
                    </h3>
                    <p className="text-sm text-gray-600">
                      ASIN: {alert.product.asin}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
