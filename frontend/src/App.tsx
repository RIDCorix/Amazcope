import { Navigate, Route, Routes } from 'react-router-dom';

// Import existing page components - we'll update their imports
import AlertsPage from '@/app/alerts/page';
import CompetitorsPage from '@/app/competitors/page';
import DashboardPage from '@/app/dashboard/page';
import LoginPage from '@/app/login/page';
import NotificationsPage from '@/app/notifications/page';
import ProductEditPage from '@/app/products/[id]/edit/page';
import ProductDetailPage from '@/app/products/[id]/page';
import ProductImportPage from '@/app/products/import/page';
import ProductsPage from '@/app/products/page';
import SettingsPage from '@/app/settings/page';
import { RootLayout } from '@/components/RootLayout';
import { Toaster } from '@/components/ui/toaster';
import SuggestionsPage from './app/suggestions/page';

function App() {
  return (
    <div className="App">
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/forgot-password"
          element={<div>Forgot Password Page</div>}
        />

        {/* Protected routes with layout */}
        <Route path="/" element={<RootLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />

          {/* Products routes */}
          <Route path="products">
            <Route index element={<ProductsPage />} />
            <Route path="import" element={<ProductImportPage />} />
            <Route path=":id" element={<ProductDetailPage />} />
            <Route path=":id/edit" element={<ProductEditPage />} />
          </Route>

          {/* Other feature routes */}
          <Route path="alerts" element={<AlertsPage />} />
          <Route path="competitors" element={<CompetitorsPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="suggestions" element={<SuggestionsPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
        </Route>

        {/* Catch-all route for 404 */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>

      {/* Global toast notifications */}
      <Toaster />
    </div>
  );
}

export default App;
