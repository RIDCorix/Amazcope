#!/usr/bin/env node
/**
 * Automated Fix Script for starscriber API calls
 *
 * This script updates all starscriberService calls in the starbook editor
 * to include the starbookSlug parameter.
 *
 * Usage: node fix-starscriber-calls.js
 */

const fs = require('fs');
const path = require('path');

const FILE_PATH = './src/app/starscriber/star-books/[slug]/page.tsx';

// Read the file
let content = fs.readFileSync(FILE_PATH, 'utf8');

// Track changes made
const changes = [];

// Fix removeDependency
const removeDependencyOld = `        const updatedTarget = await starscriberService.removeDependency(
          activeChapterSlug,
          edge.targetId,
          edge.sourceId
        );`;
const removeDependencyNew = `        const updatedTarget = await starscriberService.removeDependency(
          starbookSlug,
          activeChapterSlug,
          edge.targetId,
          edge.sourceId
        );`;
if (content.includes(removeDependencyOld)) {
  content = content.replace(removeDependencyOld, removeDependencyNew);
  changes.push('✅ Fixed removeDependency');
}

// Fix deleteNode
const deleteNodeOld = `      await starscriberService.deleteNode(activeChapterSlug, nodeId);`;
const deleteNodeNew = `      await starscriberService.deleteNode(starbookSlug, activeChapterSlug, nodeId);`;
if (content.includes(deleteNodeOld)) {
  content = content.replace(deleteNodeOld, deleteNodeNew);
  changes.push('✅ Fixed deleteNode');
}

// Fix updateNodePosition
const updateNodePositionOld = `      const updated = await starscriberService.updateNodePosition(
        activeChapterSlug,
        nodeId,
        pos.x,
        pos.y
      );`;
const updateNodePositionNew = `      const updated = await starscriberService.updateNodePosition(
        starbookSlug,
        activeChapterSlug,
        nodeId,
        pos.x,
        pos.y
      );`;
if (content.includes(updateNodePositionOld)) {
  content = content.replace(updateNodePositionOld, updateNodePositionNew);
  changes.push('✅ Fixed updateNodePosition');
}

// Fix createChapter
const createChapterOld = `      const newChapter = await starscriberService.createChapter({
        title: newChapterTitle.trim(),
        slug: slug,
        visibility: newChapterVisibility,
      });`;
const createChapterNew = `      const newChapter = await starscriberService.createChapter(
        starbookSlug,
        {
          title: newChapterTitle.trim(),
          slug: slug,
          visibility: newChapterVisibility,
        }
      );`;
if (content.includes(createChapterOld)) {
  content = content.replace(createChapterOld, createChapterNew);
  changes.push('✅ Fixed createChapter');
}

// Fix updateChapter (first occurrence - in saveChapterEdit)
const updateChapter1Old = `      const updated = await starscriberService.updateChapter(
        editingChapterSlug,
        { title: editingChapterTitle }
      );`;
const updateChapter1New = `      const updated = await starscriberService.updateChapter(
        starbookSlug,
        editingChapterSlug,
        { title: editingChapterTitle }
      );`;
if (content.includes(updateChapter1Old)) {
  content = content.replace(updateChapter1Old, updateChapter1New);
  changes.push('✅ Fixed updateChapter (saveChapterEdit)');
}

// Fix deleteChapter
const deleteChapterOld = `      await starscriberService.deleteChapter(chapterToDelete.slug);`;
const deleteChapterNew = `      await starscriberService.deleteChapter(starbookSlug, chapterToDelete.slug);`;
if (content.includes(deleteChapterOld)) {
  content = content.replace(deleteChapterOld, deleteChapterNew);
  changes.push('✅ Fixed deleteChapter');
}

// Fix updateChapter (second occurrence - in toggleChapterVisibility)
const updateChapter2Old = `      const updated = await starscriberService.updateChapter(
        chapter.slug,
        {
          visibility: chapter.visibility === 'public' ? 'private' : 'public',
        }
      );`;
const updateChapter2New = `      const updated = await starscriberService.updateChapter(
        starbookSlug,
        chapter.slug,
        {
          visibility: chapter.visibility === 'public' ? 'private' : 'public',
        }
      );`;
if (content.includes(updateChapter2Old)) {
  content = content.replace(updateChapter2Old, updateChapter2New);
  changes.push('✅ Fixed updateChapter (toggleChapterVisibility)');
}

// Fix updateNode (in detailed node editor section)
// This one might be in a nested component, need to find exact context
const updateNodePattern =
  /const updated = await starscriberService\.updateNode\(\s*activeChapterSlug,\s*node\.slug,/g;
content = content.replace(
  updateNodePattern,
  'const updated = await starscriberService.updateNode(\n                          starbookSlug,\n                          activeChapterSlug,\n                          node.slug,'
);
changes.push('✅ Fixed updateNode call(s)');

// Update dependency arrays
content = content.replace(
  /\[activeChapterSlug, nodes, toast\]/g,
  '[starbookSlug, activeChapterSlug, nodes, toast]'
);
changes.push('✅ Updated dependency arrays with starbookSlug');

content = content.replace(
  /\[activeChapterSlug, toast\]/g,
  '[starbookSlug, activeChapterSlug, toast]'
);

content = content.replace(
  /\[activeChapterSlug, graph\.edges, toast\]/g,
  '[starbookSlug, activeChapterSlug, graph.edges, toast]'
);

// Write the file back
fs.writeFileSync(FILE_PATH, content, 'utf8');

console.log('\n🎉 Successfully applied fixes:\n');
changes.forEach(change => console.log(change));
console.log(`\n📝 Updated file: ${FILE_PATH}`);
console.log(
  '\n✨ Run `npm run type-check` to verify all TypeScript errors are fixed.'
);
