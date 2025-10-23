import {
  Check,
  ChevronDown,
  ChevronUp,
  Copy,
  ExternalLink,
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

export function CategoryURLGuide() {
  const [expanded, setExpanded] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const exampleUrls = [
    {
      category: 'Electronics > Headphones',
      url: 'https://www.amazon.com/Best-Sellers-Electronics-Headphones/zgbs/electronics/172541',
    },
    {
      category: 'Home & Kitchen > Coffee Makers',
      url: 'https://www.amazon.com/Best-Sellers-Kitchen-Dining-Coffee-Machines/zgbs/kitchen/289745',
    },
    {
      category: 'Books > Fiction',
      url: 'https://www.amazon.com/Best-Sellers-Books-Literature-Fiction/zgbs/books/17',
    },
  ];

  const handleCopy = async (url: string, index: number) => {
    try {
      await navigator.clipboard.writeText(url);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              📚 How to Find Category URLs
              <Badge variant="secondary">Guide</Badge>
            </CardTitle>
            <CardDescription>
              Learn how to get Amazon category URLs for bestseller tracking
            </CardDescription>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </Button>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="space-y-4">
          {/* Step-by-step instructions */}
          <div className="space-y-3">
            <div className="flex gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-bold flex-shrink-0">
                1
              </div>
              <div>
                <h4 className="font-medium mb-1">Go to Amazon Best Sellers</h4>
                <p className="text-sm text-gray-600">
                  Visit{' '}
                  <a
                    href="https://www.amazon.com/Best-Sellers/zgbs"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline inline-flex items-center gap-1"
                  >
                    amazon.com/Best-Sellers
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-bold flex-shrink-0">
                2
              </div>
              <div>
                <h4 className="font-medium mb-1">Navigate to Category</h4>
                <p className="text-sm text-gray-600">
                  Use the left sidebar to browse to the specific category you
                  want to track (e.g., Electronics → Headphones → Wireless
                  Earbuds)
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-bold flex-shrink-0">
                3
              </div>
              <div>
                <h4 className="font-medium mb-1">Copy the URL</h4>
                <p className="text-sm text-gray-600">
                  Once you&apos;re on the category page, copy the URL from your
                  browser&apos;s address bar. It should contain{' '}
                  <code className="bg-gray-100 px-1 rounded">/zgbs/</code>
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-bold flex-shrink-0">
                4
              </div>
              <div>
                <h4 className="font-medium mb-1">Paste into Form</h4>
                <p className="text-sm text-gray-600">
                  Paste the URL into the &quot;Category URL&quot; field when
                  importing a product or updating category settings
                </p>
              </div>
            </div>
          </div>

          {/* Example URLs */}
          <div className="border-t pt-4">
            <h4 className="font-medium mb-3">Example Category URLs:</h4>
            <div className="space-y-2">
              {exampleUrls.map((example, index) => (
                <div
                  key={index}
                  className="p-3 border rounded-md bg-gray-50 hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="text-sm font-medium text-gray-700">
                      {example.category}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 px-2"
                      onClick={() => handleCopy(example.url, index)}
                    >
                      {copiedIndex === index ? (
                        <>
                          <Check className="w-3 h-3 mr-1" />
                          Copied
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3 mr-1" />
                          Copy
                        </>
                      )}
                    </Button>
                  </div>
                  <div className="text-xs text-gray-600 font-mono break-all">
                    {example.url}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Tips */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <h4 className="font-medium text-blue-900 mb-2">💡 Tips:</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>
                • More specific categories give better competitive insights
              </li>
              <li>
                • Category URLs work across all Amazon marketplaces (.com,
                .co.uk, .de, etc.)
              </li>
              <li>
                • Manual categories override auto-detected ones, giving you full
                control
              </li>
              <li>
                • Bestseller data refreshes automatically when you provide a
                category URL
              </li>
            </ul>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
