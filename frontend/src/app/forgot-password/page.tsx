import { AlertCircle, ArrowLeft, CheckCircle2, Mail } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useTranslation } from '@/hooks/useTranslation';

export default function ForgotPasswordPage() {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // TODO: Implement password reset API call
      // await authService.requestPasswordReset(email);

      // Simulate API call for now
      await new Promise(resolve => setTimeout(resolve, 1500));
      setSubmitted(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.forgotPassword.error'));
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-4">
        <Card className="w-full max-w-md shadow-xl border-0">
          <CardHeader className="space-y-2 text-center pb-8">
            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-2">
              <CheckCircle2 className="h-8 w-8 text-green-600" />
            </div>
            <CardTitle className="text-2xl font-bold text-slate-900">
              {t('auth.forgotPassword.checkEmail')}
            </CardTitle>
            <CardDescription className="text-base">
              {t('auth.forgotPassword.emailSent')} <strong>{email}</strong>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-600 text-center">
              {t('auth.forgotPassword.checkSpam')}
            </p>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4 border-t pt-6">
            <Link to="/login" className="w-full">
              <Button
                variant="outline"
                className="w-full h-11 border-slate-300"
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                {t('auth.forgotPassword.backToLogin')}
              </Button>
            </Link>
            <button
              onClick={() => {
                setSubmitted(false);
                setEmail('');
              }}
              className="text-sm text-blue-600 hover:text-blue-700 hover:underline transition-colors"
            >
              {t('auth.forgotPassword.tryDifferent')}
            </button>
          </CardFooter>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md shadow-xl border-0">
        <CardHeader className="space-y-2 text-center pb-8">
          <div className="mx-auto w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center mb-2">
            <span className="text-2xl font-bold text-white">A</span>
          </div>
          <CardTitle className="text-2xl font-bold text-slate-900">
            {t('auth.forgotPassword.title')}
          </CardTitle>
          <CardDescription className="text-base">
            {t('auth.forgotPassword.subtitle')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="flex items-start gap-3 p-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg animate-in fade-in slide-in-from-top-1 duration-300">
                <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                <p className="flex-1">{error}</p>
              </div>
            )}

            <div className="space-y-2">
              <Label
                htmlFor="email"
                className="text-sm font-medium text-slate-700"
              >
                {t('auth.forgotPassword.email')}
              </Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <Input
                  id="email"
                  type="email"
                  placeholder={t('auth.forgotPassword.emailPlaceholder')}
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                  disabled={loading}
                  className="pl-10 h-11 border-slate-300 focus:border-blue-500 focus:ring-blue-500"
                  autoComplete="email"
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full h-11 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-medium shadow-md hover:shadow-lg transition-all duration-200"
              disabled={loading}
            >
              {loading
                ? t('auth.forgotPassword.sending')
                : t('auth.forgotPassword.sendInstructions')}
            </Button>
          </form>
        </CardContent>

        <CardFooter className="flex flex-col space-y-4 border-t pt-6">
          <Link to="/login" className="w-full">
            <Button
              variant="ghost"
              className="w-full h-11 text-slate-600 hover:text-slate-900"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              {t('auth.forgotPassword.backToLogin')}
            </Button>
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
}
