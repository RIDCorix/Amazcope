#!/bin/bash

# Remove 'use client' directives from all TypeScript/JavaScript React files
cd /Users/youngray/amazcope/frontend/src

# Find all .tsx and .ts files and remove 'use client' directive
find . -type f \( -name "*.tsx" -o -name "*.ts" \) -exec sed -i '' "/^'use client';$/d" {} \;

echo "Removed 'use client' directives from all files"
