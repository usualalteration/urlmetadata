import { ExternalLink, Globe } from "lucide-react";
import type { MetadataItem } from "@/lib/api";

interface MetadataCardProps {
  item: MetadataItem;
}

// Display a single extracted URL as a social-preview style card.
const MetadataCard = ({ item }: MetadataCardProps) => {
  const { title, description, favicon, image, url, cached } = item;

  // Derive a display hostname from the URL for readability.
  let hostname = url;
  try {
    hostname = new URL(url).hostname.replace(/^www\./, "");
  } catch {
    // keep raw url if parsing fails
  }

  return (
    <article className="group flex flex-col overflow-hidden rounded-2xl border bg-card shadow-sm transition-shadow hover:shadow-md">
      {/* Preview image (Open Graph image) */}
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="block aspect-video w-full overflow-hidden bg-muted"
        aria-label={`Apri ${title || url}`}
      >
        {image ? (
          <img
            src={image}
            alt={title || hostname}
            loading="lazy"
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
            onError={(e) => {
              // Hide broken preview images gracefully.
              (e.currentTarget as HTMLImageElement).style.display = "none";
            }}
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-muted-foreground">
            <Globe className="h-10 w-10" />
          </div>
        )}
      </a>

      {/* Body: favicon + title, description, link */}
      <div className="flex flex-1 flex-col gap-2 p-4">
        <div className="flex items-start gap-2">
          {favicon ? (
            <img
              src={favicon}
              alt=""
              aria-hidden="true"
              className="mt-0.5 h-5 w-5 shrink-0 rounded-sm"
              onError={(e) => {
                (e.currentTarget as HTMLImageElement).style.display = "none";
              }}
            />
          ) : (
            <Globe className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" />
          )}
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="line-clamp-2 text-base font-semibold leading-snug text-foreground hover:text-primary"
          >
            {title || hostname}
          </a>
        </div>

        {description ? (
          <p className="line-clamp-3 text-sm text-muted-foreground">{description}</p>
        ) : (
          <p className="text-sm italic text-muted-foreground/70">
            Nessuna descrizione disponibile
          </p>
        )}

        <div className="mt-auto flex items-center justify-between gap-2 pt-2">
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-primary"
          >
            <ExternalLink className="h-3 w-3" />
            <span className="truncate">{hostname}</span>
          </a>
          {cached ? (
            <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-600">
              cached
            </span>
          ) : null}
        </div>
      </div>
    </article>
  );
};

export default MetadataCard;