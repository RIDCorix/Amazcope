import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function NotFound() {
  const navigate = useNavigate();

  useEffect(() => {
    // For SPA routing, redirect 404s to the current path
    // This allows client-side routing to handle the route
    const currentPath = window.location.pathname;

    // If it's already the home page, don't redirect
    if (currentPath === '/') {
      return;
    }

    // For static export, we need to handle client-side routing manually
    // This will allow the client-side router to take over
    navigate(currentPath);
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h2 className="text-2xl font-semibold mb-4">Loading...</h2>
        <p className="text-gray-600">Initializing application...</p>
      </div>
    </div>
  );
}
