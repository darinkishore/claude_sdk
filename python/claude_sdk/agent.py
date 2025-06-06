"""High-level Python wrapper for Claude SDK execution engine."""

from pathlib import Path
from typing import Optional, List, Union
from dataclasses import dataclass
from datetime import datetime

from . import Workspace, Conversation, Transition, Message, Session


@dataclass
class AgentResponse:
    """User-friendly response wrapper for Claude executions."""
    
    def __init__(self, transition: Transition):
        self._transition = transition
    
    @property
    def text(self) -> str:
        """The Claude response text."""
        return self._transition.execution.response
    
    @property
    def session_id(self) -> str:
        """The session ID for this execution."""
        return self._transition.execution.session_id
    
    @property
    def files_created(self) -> List[Path]:
        """Files that were created in this execution."""
        before_files = set(self._transition.before.files.keys())
        after_files = set(self._transition.after.files.keys())
        return [Path(f) for f in sorted(after_files - before_files)]
    
    @property
    def files_modified(self) -> List[Path]:
        """Files that were modified in this execution."""
        before_files = self._transition.before.files
        after_files = self._transition.after.files
        
        modified = []
        for path, content in after_files.items():
            if path in before_files and before_files[path] != content:
                modified.append(Path(path))
        return sorted(modified)
    
    @property
    def files_deleted(self) -> List[Path]:
        """Files that were deleted in this execution."""
        before_files = set(self._transition.before.files.keys())
        after_files = set(self._transition.after.files.keys())
        return [Path(f) for f in sorted(before_files - after_files)]
    
    @property
    def all_files_changed(self) -> List[Path]:
        """All files that changed (created, modified, or deleted)."""
        return sorted(set(self.files_created + self.files_modified + self.files_deleted))
    
    @property
    def cost(self) -> float:
        """Cost in USD for this execution."""
        return self._transition.execution.cost
    
    @property
    def duration_ms(self) -> int:
        """Duration in milliseconds."""
        return self._transition.execution.duration_ms
    
    @property
    def tools_used(self) -> List[str]:
        """List of tools used in this execution."""
        return self._transition.tools_used()
    
    @property
    def has_errors(self) -> bool:
        """Whether any tools had errors."""
        return self._transition.has_tool_errors()
    
    @property
    def messages(self) -> List[Message]:
        """Fully-typed Claude messages added in this turn.
        
        The list preserves Claude's internal order:
        [user_msg, assistant_thinking?, assistant_reply, ...]
        """
        return self._transition.new_messages()
    
    @property
    def session_after(self) -> Optional[Session]:
        """Complete Claude session state after this turn."""
        return self._transition.session_after
    
    @property
    def transition(self) -> Transition:
        """Access the underlying transition for advanced use."""
        return self._transition
    
    def __str__(self) -> str:
        """String representation shows the response text."""
        return self.text
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"AgentResponse("
            f"cost=${self.cost:.4f}, "
            f"duration={self.duration_ms}ms, "
            f"tools={len(self.tools_used)}, "
            f"files_changed={len(self.all_files_changed)})"
        )


class ClaudeAgent:
    """High-level interface for interacting with Claude.
    
    This provides a simple, intuitive API for common tasks while still
    allowing access to the full power of the execution engine.
    
    Example:
        agent = ClaudeAgent("/path/to/project")
        response = agent.send("Build a TODO app")
        print(response.text)
        print(f"Created files: {response.files_created}")
    """
    
    def __init__(
        self, 
        workspace: Union[str, Path], 
        auto_continue: bool = True,
        record_transitions: bool = True
    ):
        """Initialize a Claude agent.
        
        Args:
            workspace: Path to the workspace directory
            auto_continue: Whether to automatically continue conversations (default: True)
            record_transitions: Whether to persist transitions to disk (default: True)
        """
        self.workspace = Workspace(str(workspace))
        self.conversation = Conversation(self.workspace, record=record_transitions)
        self.auto_continue = auto_continue
        self._responses: List[AgentResponse] = []
    
    def send(self, message: str, continue_: Optional[bool] = None) -> AgentResponse:
        """Send a message to Claude.
        
        Args:
            message: The message to send
            continue_: Whether to continue the conversation (overrides auto_continue)
            
        Returns:
            AgentResponse with the results
        """
        should_continue = continue_ if continue_ is not None else self.auto_continue
        
        if not should_continue and len(self._responses) > 0:
            # Start a new conversation
            self.conversation = Conversation(
                self.workspace, 
                record=hasattr(self.conversation, 'recorder') and self.conversation.recorder is not None
            )
            self._responses = []
        
        # Execute via conversation
        transition = self.conversation.send(message)
        response = AgentResponse(transition)
        self._responses.append(response)
        
        return response
    
    def new_conversation(self) -> None:
        """Start a new conversation, clearing history."""
        record = hasattr(self.conversation, 'recorder') and self.conversation.recorder is not None
        self.conversation = Conversation(self.workspace, record=record)
        self._responses = []
    
    @property
    def history(self) -> List[AgentResponse]:
        """Get all responses in the current conversation."""
        return self._responses.copy()
    
    @property
    def total_cost(self) -> float:
        """Total cost of all executions in current conversation."""
        return self.conversation.total_cost
    
    @property
    def session_ids(self) -> List[str]:
        """All session IDs in the current conversation."""
        return self.conversation.session_ids
    
    def save_conversation(self, path: Union[str, Path]) -> None:
        """Save the current conversation to disk.
        
        Args:
            path: Where to save the conversation
        """
        self.conversation.save(str(path))
    
    @classmethod
    def load_conversation(
        cls,
        path: Union[str, Path],
        workspace: Union[str, Path],
        auto_continue: bool = True,
        record_transitions: bool = True
    ) -> 'ClaudeAgent':
        """Load a conversation from disk.
        
        Args:
            path: Path to the saved conversation
            workspace: Workspace path (must match the original)
            auto_continue: Whether to auto-continue loaded conversation
            record_transitions: Enable recording for the loaded conversation
            
        Returns:
            ClaudeAgent with the loaded conversation
        """
        workspace_obj = Workspace(str(workspace))
        conversation = Conversation.load(str(path), workspace_obj, record=record_transitions)
        
        agent = cls.__new__(cls)
        agent.workspace = workspace_obj
        agent.conversation = conversation
        agent.auto_continue = auto_continue
        
        # Rebuild responses from conversation history
        agent._responses = [
            AgentResponse(transition) 
            for transition in conversation.history()
        ]
        
        return agent
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ClaudeAgent("
            f"workspace='{self.workspace.path}', "
            f"cost=${self.total_cost:.4f}, "
            f"messages={len(self._responses)})"
        )


class ClaudeEnvironment:
    """Environment for stateful, checkpoint-based execution.
    
    This is useful for exploration, testing different approaches,
    or implementing RL-style algorithms.
    
    Example:
        env = ClaudeEnvironment("/workspace")
        
        # Save current state
        checkpoint = env.checkpoint()
        
        # Try something
        response = env.send("Build with React")
        
        # Restore if needed
        env.restore(checkpoint)
        
        # Try different approach
        response = env.send("Build with Vue")
    """
    
    def __init__(self, workspace: Union[str, Path]):
        """Initialize environment.
        
        Args:
            workspace: Path to workspace directory
        """
        self.workspace_path = Path(workspace)
        self.workspace = Workspace(str(workspace))
        self._checkpoints: List[tuple[str, Conversation]] = []
    
    def checkpoint(self, name: Optional[str] = None) -> str:
        """Save current state.
        
        Args:
            name: Optional checkpoint name
            
        Returns:
            Checkpoint ID
        """
        if name is None:
            name = f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save current conversation state
        conv_path = self.workspace_path / ".claude-sdk" / "checkpoints" / f"{name}.json"
        conv_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a new conversation at current state
        current_conv = Conversation(self.workspace)
        current_conv.save(str(conv_path))
        
        self._checkpoints.append((name, current_conv))
        return name
    
    def restore(self, checkpoint_id: str) -> None:
        """Restore to a checkpoint.
        
        Args:
            checkpoint_id: The checkpoint to restore
        """
        # TODO: Implement this
        raise NotImplementedError("File system restoration not yet implemented")
    
    def send(self, message: str) -> AgentResponse:
        """Send a message in current state.
        
        Args:
            message: Message to send
            
        Returns:
            AgentResponse
        """
        conversation = Conversation(self.workspace)
        transition = conversation.send(message)
        return AgentResponse(transition)
    
    def explore_from(
        self, 
        checkpoint_id: str, 
        message: str
    ) -> tuple[str, AgentResponse]:
        # TODO: Implement this
        raise NotImplementedError("Explore from a checkpoint is not implemented")
        """Explore from a checkpoint without changing current state.
        
        Args:
            checkpoint_id: Starting checkpoint
            message: Message to send
            
        Returns:
            Tuple of (new_checkpoint_id, response)
        """
        # This would restore the checkpoint in a temporary workspace
        # For now, we demonstrate the API
        temp_workspace = Workspace(str(self.workspace_path))
        temp_conv = Conversation(temp_workspace)
        
        transition = temp_conv.send(message)
        response = AgentResponse(transition)
        
        # Save as new checkpoint
        new_checkpoint = self.checkpoint(f"{checkpoint_id}_explore")
        
        return new_checkpoint, response