/**
 * Verification for task execution.
 */

import { spawn } from 'child_process';
import { join } from 'path';
import { Task } from '../core/task.js';
import { VerificationError } from '../utils/errors.js';

/**
 * Normalize command tokens when they still include the task run_path prefix.
 * This keeps backwards compatibility with commands like
 * "python3 TOOLS/001/verify.py" while running from that task directory.
 */
function stripRunPathPrefix(token: string, runPath: string): string {
  const withSlash = `${runPath}/`;
  if (token.startsWith(withSlash)) {
    return token.slice(withSlash.length);
  }

  const withDotSlash = `./${runPath}/`;
  if (token.startsWith(withDotSlash)) {
    return token.slice(withDotSlash.length);
  }

  return token;
}

/**
 * Verification result.
 */
export interface VerificationResult {
  passed: boolean;
  exitCode: number | null;
  stdout: string;
  stderr: string;
  durationSecs: number;
}

/**
 * Verifier for running task verification commands.
 */
export class Verifier {
  /**
   * Run verification for a task in the given workspace.
   * @param task The task to verify
   * @param workspace The workspace root path
   * @returns Verification result
   */
  static async verify(task: Task, workspace: string): Promise<VerificationResult> {
    const startTime = Date.now();

    // Parse the command
    const commandParts = task.verification.command.match(/(?:[^\s"]+|"[^"]*")+/g) || [];
    if (commandParts.length === 0) {
      throw new VerificationError('Empty verification command');
    }

    const verificationCwd = join(workspace, task.source.run_path);
    const firstToken = commandParts[0];
    if (!firstToken) {
      throw new VerificationError('Empty verification command');
    }
    const program = stripRunPathPrefix(firstToken.replace(/"/g, ''), task.source.run_path);
    const args = commandParts
      .slice(1)
      .map(arg => stripRunPathPrefix(arg.replace(/"/g, ''), task.source.run_path));

    // Execute command with timeout
    return new Promise((resolve, reject) => {
      const proc = spawn(program, args, {
        cwd: verificationCwd,
        timeout: task.verification.timeout * 1000, // Convert to milliseconds
      });

      let stdout = '';
      let stderr = '';

      proc.stdout?.on('data', (data) => {
        stdout += data.toString();
      });

      proc.stderr?.on('data', (data) => {
        stderr += data.toString();
      });

      proc.on('close', (code) => {
        const durationSecs = (Date.now() - startTime) / 1000;
        resolve({
          passed: code === 0,
          exitCode: code,
          stdout,
          stderr,
          durationSecs,
        });
      });

      proc.on('error', (error) => {
        // Check if it's a timeout error
        if ((error as any).code === 'ETIMEDOUT') {
          reject(
            new VerificationError(
              `Verification command timed out after ${task.verification.timeout} seconds`
            )
          );
        } else {
          reject(new VerificationError(`Failed to execute verification command: ${error.message}`));
        }
      });

      // Additional timeout handling
      const timeoutId = setTimeout(() => {
        proc.kill('SIGTERM');
        reject(
          new VerificationError(
            `Verification command timed out after ${task.verification.timeout} seconds`
          )
        );
      }, task.verification.timeout * 1000);

      proc.on('close', () => {
        clearTimeout(timeoutId);
      });
    });
  }
}
