import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import type { PodcastProjectCreate } from '@/lib/api/types';
import { usePodcasts } from '@/lib/hooks/usePodcasts';

const SAMPLE_SCRIPT = `---
title: My First Podcast
episode: "Episode 1"
speakers:
  host1: "Sarah"
  guest1: "John"
description: "A conversation about AI and technology"
---

host1: Welcome to our podcast! Today we're discussing AI.

guest1: It's exciting to see how AI is changing our world.

host1: Absolutely, let's dive deeper into this topic.

guest1: I think the key is understanding both the opportunities and challenges.

[sound_effect: applause]

host1: Thank you for tuning in! See you next time.
`;

interface CreatePodcastDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreatePodcastDialog({ open, onOpenChange }: CreatePodcastDialogProps) {
  const { createProject } = usePodcasts();
  const [scriptContent, setScriptContent] = useState(SAMPLE_SCRIPT);
  const [creating, setCreating] = useState(false);

  const handleCreate = async () => {
    setCreating(true);
    try {
      const data: PodcastProjectCreate = {
        script_content: scriptContent,
      };

      await createProject(data);
      onOpenChange(false);
      setScriptContent(SAMPLE_SCRIPT);
    } catch (err) {
      console.error('Failed to create project:', err);
    } finally {
      setCreating(false);
    }
  };

  const handleLoadTemplate = () => {
    setScriptContent(SAMPLE_SCRIPT);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Create New Podcast Project</DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto py-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label>Podcast Script (Markdown)</Label>
              <Button variant="ghost" size="sm" onClick={handleLoadTemplate}>
                Load Template
              </Button>
            </div>

            <div className="bg-muted/50 rounded-lg p-4">
              <Textarea
                value={scriptContent}
                onChange={(e) => setScriptContent(e.target.value)}
                placeholder="Paste your podcast script here..."
                className="min-h-[300px] font-mono text-sm leading-relaxed"
              />
            </div>

            <div className="text-sm text-muted-foreground space-y-1">
              <p className="font-medium">Script Format:</p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>
                  Use <code className="bg-muted px-1 py-0.5 rounded text-xs">---</code> to begin
                  frontmatter
                </li>
                <li>Include title, speakers, and other metadata in frontmatter</li>
                <li>
                  Use <code className="bg-muted px-1 py-0.5 rounded text-xs">speaker:</code> for
                  dialogue lines
                </li>
                <li>
                  Use{' '}
                  <code className="bg-muted px-1 py-0.5 rounded text-xs">[sound_effect: name]</code>{' '}
                  for effects
                </li>
              </ul>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleCreate} disabled={creating || !scriptContent.trim()}>
            {creating ? 'Creating...' : 'Create Project'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
