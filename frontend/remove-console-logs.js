#!/usr/bin/env node

/**
 * Script to remove all console.log statements from TypeScript/JavaScript files
 * Usage: node remove-console-logs.js
 */

const fs = require('fs');
const path = require('path');

const srcDir = path.join(__dirname, 'src');
let filesProcessed = 0;
let filesModified = 0;
let logsRemoved = 0;

/**
 * Recursively find all .ts, .tsx, .js, .jsx files
 */
function findFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);

  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (stat.isDirectory()) {
      // Skip node_modules and .next directories
      if (file !== 'node_modules' && file !== '.next' && file !== 'dist') {
        findFiles(filePath, fileList);
      }
    } else if (/\.(ts|tsx|js|jsx)$/.test(file)) {
      fileList.push(filePath);
    }
  });

  return fileList;
}

/**
 * Remove console.log statements from content
 */
function removeConsoleLogs(content) {
  let modified = false;
  let removedCount = 0;
  const originalContent = content;

  // Pattern 1: Multi-line console.log (most comprehensive, run first)
  // Matches console.log( ... ) across multiple lines with proper bracket matching
  let iterations = 0;
  const maxIterations = 100; // Safety limit

  while (iterations < maxIterations) {
    iterations++;
    const prevContent = content;

    // Find console.log with balanced parentheses
    const consoleLogRegex = /console\.log\s*\(/g;
    const match = consoleLogRegex.exec(content);

    if (!match) break;

    // Check if this is at the start of a line (with optional whitespace)
    const lineStart = content.lastIndexOf('\n', match.index) + 1;
    const beforeMatch = content.slice(lineStart, match.index);
    const isStandalone = /^\s*$/.test(beforeMatch);

    const startPos = isStandalone ? lineStart : match.index;
    let pos = match.index + match[0].length;
    let depth = 1;
    let foundEnd = false;

    // Find the matching closing parenthesis
    while (pos < content.length && depth > 0) {
      const char = content[pos];
      if (char === '(') depth++;
      else if (char === ')') {
        depth--;
        if (depth === 0) {
          foundEnd = true;
          pos++; // Include the closing paren
          // Skip optional semicolon
          if (content[pos] === ';') pos++;
          // If standalone, skip to end of line
          if (isStandalone) {
            while (
              pos < content.length &&
              (content[pos] === ' ' || content[pos] === '\t')
            ) {
              pos++;
            }
            if (content[pos] === '\n' || content[pos] === '\r') {
              pos++;
              if (content[pos] === '\n') pos++; // Handle \r\n
            }
          }
          break;
        }
      } else if (char === '"' || char === "'" || char === '`') {
        // Skip string literals
        const quote = char;
        pos++;
        while (pos < content.length) {
          if (content[pos] === '\\') {
            pos += 2; // Skip escaped character
          } else if (content[pos] === quote) {
            pos++;
            break;
          } else {
            pos++;
          }
        }
        continue;
      }
      pos++;
    }

    if (foundEnd) {
      // Remove the console.log statement
      content = content.slice(0, startPos) + content.slice(pos);
      removedCount++;
      modified = true;
    } else {
      // Couldn't find matching paren, skip this match
      break;
    }
  }

  // Pattern 2: Inline console.log (in the middle of a line)
  const inlinePattern = /;\s*console\.log\([^)]*\);?/g;
  const inlineMatches = content.match(inlinePattern);
  if (inlineMatches) {
    removedCount += inlineMatches.length;
    content = content.replace(inlinePattern, ';');
    modified = true;
  }

  // Clean up empty if blocks left after console.log removal
  // Matches: if (...) {\n  \n}
  content = content.replace(/if\s*\([^)]+\)\s*\{\s*\n\s*\}/gm, '');

  // Clean up multiple consecutive empty lines (max 2 empty lines)
  content = content.replace(/\n\s*\n\s*\n\s*\n/g, '\n\n\n');

  // Final check if anything changed
  if (content !== originalContent) {
    modified = true;
  }

  return { content, modified, removedCount };
}

/**
 * Process a single file
 */
function processFile(filePath) {
  filesProcessed++;

  try {
    const originalContent = fs.readFileSync(filePath, 'utf8');
    const {
      content: newContent,
      modified,
      removedCount,
    } = removeConsoleLogs(originalContent);

    if (modified) {
      fs.writeFileSync(filePath, newContent, 'utf8');
      filesModified++;
      logsRemoved += removedCount;
      const relativePath = path.relative(process.cwd(), filePath);
      console.log(`✓ ${relativePath} - Removed ${removedCount} console.log(s)`);
    }
  } catch (error) {
    console.error(`✗ Error processing ${filePath}:`, error.message);
  }
}

/**
 * Main execution
 */
function main() {
  console.log('🔍 Searching for TypeScript/JavaScript files...\n');

  const files = findFiles(srcDir);
  console.log(`Found ${files.length} files to process\n`);

  console.log('🧹 Removing console.log statements...\n');

  files.forEach(processFile);

  console.log('\n' + '='.repeat(60));
  console.log('📊 Summary:');
  console.log('='.repeat(60));
  console.log(`Files processed: ${filesProcessed}`);
  console.log(`Files modified: ${filesModified}`);
  console.log(`Total console.log statements removed: ${logsRemoved}`);
  console.log('='.repeat(60));

  if (filesModified === 0) {
    console.log('\n✨ No console.log statements found. Code is clean!');
  } else {
    console.log('\n✨ Done! All console.log statements have been removed.');
  }
}

// Run the script
main();
