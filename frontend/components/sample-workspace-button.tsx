"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { toast } from "sonner";

import { provisionSampleWorkspace } from "@/lib/api";

export function SampleWorkspaceButton({ className = "button button-secondary" }: { className?: string }) {
  const queryClient = useQueryClient();
  const sampleWorkspace = useMutation({
    mutationFn: provisionSampleWorkspace,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["meetings"] }),
        queryClient.invalidateQueries({ queryKey: ["calendar-meetings"] }),
        queryClient.invalidateQueries({ queryKey: ["team-meetings"] }),
      ]);
      toast.success("Sample workspace is ready");
    },
    onError: () => toast.error("Could not create the sample workspace"),
  });

  return (
    <button
      className={className}
      type="button"
      disabled={sampleWorkspace.isPending}
      onClick={() => sampleWorkspace.mutate()}
    >
      <Sparkles size={16} />
      {sampleWorkspace.isPending ? "Preparing sample..." : "Explore sample workspace"}
    </button>
  );
}
