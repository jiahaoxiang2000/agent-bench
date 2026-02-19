/**
 * Task loader for discovering and loading benchmark tasks.
 */

import { readdir, readFile } from 'fs/promises';
import { join } from 'path';
import yaml from 'js-yaml';
import { Task, TaskRawSchema, resolveTask } from './task.js';
import { TaskLoadError, TaskNotFoundError } from '../utils/errors.js';

/**
 * Task loader for discovering and loading benchmark tasks.
 */
export class TaskLoader {
  private tasksDir: string;

  constructor(tasksDir: string) {
    this.tasksDir = tasksDir;
  }

  /**
   * Load all tasks from the tasks directory.
   */
  async loadAll(): Promise<Task[]> {
    const tasks: Task[] = [];

    try {
      await this.loadRecursive(this.tasksDir, tasks);
    } catch (error) {
      // If directory doesn't exist, return empty array
      if ((error as any)?.code === 'ENOENT') {
        return tasks;
      }
      throw error;
    }

    return tasks;
  }

  /**
   * Recursively load tasks from a directory.
   */
  private async loadRecursive(directory: string, tasks: Task[]): Promise<void> {
    const entries = await readdir(directory, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = join(directory, entry.name);

      if (entry.isDirectory()) {
        await this.loadRecursive(fullPath, tasks);
      } else if (entry.name === 'task.yaml' || entry.name === 'task.yml') {
        try {
          const task = await this.loadFromFile(fullPath);
          tasks.push(task);
        } catch (error) {
          console.warn(`Warning: Failed to load ${fullPath}:`, error);
        }
      }
    }
  }

  /**
   * Load a task from a YAML file.
   * Parses only the fields stored in the YAML, then derives source repository
   * details, run_path, and verification command from the task ID.
   */
  private async loadFromFile(filePath: string): Promise<Task> {
    try {
      const content = await readFile(filePath, 'utf-8');
      const data = yaml.load(content);

      // Parse only the fields present in the YAML
      const raw = TaskRawSchema.parse(data);
      // Derive source, run_path, and verification command from the task ID
      return resolveTask(raw);
    } catch (error) {
      if ((error as any)?.code === 'ENOENT') {
        throw new TaskLoadError(`Failed to read ${filePath}: file not found`);
      }
      throw new TaskLoadError(`Failed to load ${filePath}: ${error}`);
    }
  }

  /**
   * Load a specific task by ID.
   */
  async loadById(taskId: string): Promise<Task> {
    const tasks = await this.loadAll();
    const task = tasks.find(t => t.id === taskId);

    if (!task) {
      throw new TaskNotFoundError(`Task ${taskId} not found`);
    }

    return task;
  }

  /**
   * List all available task IDs.
   */
  async listIds(): Promise<string[]> {
    const tasks = await this.loadAll();
    return tasks.map(t => t.id);
  }

  /**
   * Filter tasks by category.
   */
  async filterByCategory(category: string): Promise<Task[]> {
    const tasks = await this.loadAll();
    return tasks.filter(t => t.category === category);
  }

  /**
   * Filter tasks by difficulty.
   */
  async filterByDifficulty(difficulty: string): Promise<Task[]> {
    const tasks = await this.loadAll();
    return tasks.filter(t => t.difficulty === difficulty);
  }

  /**
   * Filter tasks by tags.
   */
  async filterByTags(tags: string[]): Promise<Task[]> {
    const tasks = await this.loadAll();
    return tasks.filter(task => {
      const taskTags = task.metadata?.tags || [];
      return tags.some(tag => taskTags.includes(tag));
    });
  }
}
