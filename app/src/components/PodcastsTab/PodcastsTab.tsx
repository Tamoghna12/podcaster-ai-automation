import { PodcastEditor } from './PodcastEditor';
import { PodcastList } from './PodcastList';

export function PodcastTab() {
  return (
    <div className="flex flex-col h-full min-h-0 overflow-hidden">
      {/* Main content area */}
      <div className="flex-1 min-h-0 flex gap-6 overflow-hidden relative">
        {/* Left Column - Project List */}
        <div className="flex flex-col min-h-0 overflow-hidden w-full max-w-[360px] shrink-0">
          <PodcastList />
        </div>

        {/* Right Column - Project Editor */}
        <div className="flex flex-col min-h-0 overflow-hidden flex-1">
          <PodcastEditor />
        </div>
      </div>
    </div>
  );
}
