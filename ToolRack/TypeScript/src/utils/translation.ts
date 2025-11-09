// Unix to Windows command translation

interface CommandTranslation {
  command: string;
  args?: string[];
  modifier?: (originalArgs: string[]) => string[];
}

const commandTranslations: Record<string, CommandTranslation> = {
  'ls': {
    command: 'dir',
    modifier: (args) => {
      // Translate common ls flags to dir equivalents
      const newArgs: string[] = [];
      for (const arg of args) {
        if (arg === '-la' || arg === '-al') {
          newArgs.push('/a');
        } else if (arg === '-l') {
          // dir shows detailed info by default
          continue;
        } else if (arg === '-a') {
          newArgs.push('/a');
        } else if (arg.startsWith('-')) {
          // Skip other Unix flags that don't have Windows equivalents
          continue;
        } else {
          newArgs.push(arg);
        }
      }
      return newArgs;
    }
  },
  'cat': {
    command: 'type'
  },
  'grep': {
    command: 'findstr',
    modifier: (args) => {
      // Basic grep to findstr translation
      const newArgs: string[] = [];
      for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        if (arg === '-i') {
          newArgs.push('/i');
        } else if (arg === '-n') {
          newArgs.push('/n');
        } else if (arg === '-r' || arg === '-R') {
          newArgs.push('/s');
        } else if (!arg.startsWith('-')) {
          newArgs.push(arg);
        }
      }
      return newArgs;
    }
  },
  'find': {
    command: 'dir',
    modifier: (args) => {
      // Basic find to dir translation
      const newArgs = ['/s', '/b'];
      for (const arg of args) {
        if (!arg.startsWith('-') && arg !== '.') {
          newArgs.push(arg);
        }
      }
      return newArgs;
    }
  },
  'cp': {
    command: 'copy'
  },
  'mv': {
    command: 'move'
  },
  'rm': {
    command: 'del',
    modifier: (args) => {
      const newArgs: string[] = [];
      for (const arg of args) {
        if (arg === '-r' || arg === '-rf') {
          newArgs.push('/s');
        } else if (arg === '-f') {
          newArgs.push('/f');
        } else if (!arg.startsWith('-')) {
          newArgs.push(arg);
        }
      }
      return newArgs;
    }
  },
  'mkdir': {
    command: 'mkdir'
  },
  'rmdir': {
    command: 'rmdir',
    modifier: (args) => {
      const newArgs: string[] = [];
      for (const arg of args) {
        if (arg === '-r') {
          newArgs.push('/s');
        } else if (!arg.startsWith('-')) {
          newArgs.push(arg);
        }
      }
      return newArgs;
    }
  },
  'pwd': {
    command: 'cd'
  },
  'which': {
    command: 'where'
  },
  'ps': {
    command: 'tasklist'
  },
  'kill': {
    command: 'taskkill',
    modifier: (args) => {
      const newArgs: string[] = [];
      for (const arg of args) {
        if (arg === '-9') {
          newArgs.push('/f');
        } else if (!arg.startsWith('-')) {
          newArgs.push('/pid', arg);
        }
      }
      return newArgs;
    }
  },
  'touch': {
    command: 'echo',
    modifier: (args) => {
      // touch file -> echo. > file (creates empty file)
      if (args.length > 0) {
        return ['.', '>', args[0]];
      }
      return args;
    }
  },
  'head': {
    command: 'powershell',
    modifier: (args) => {
      if (args.length > 0) {
        const lines = args.find(arg => arg.startsWith('-n'))?.replace('-n', '') || '10';
        const file = args.find(arg => !arg.startsWith('-')) || '';
        return ['-Command', `Get-Content "${file}" | Select-Object -First ${lines}`];
      }
      return args;
    }
  },
  'tail': {
    command: 'powershell',
    modifier: (args) => {
      if (args.length > 0) {
        const lines = args.find(arg => arg.startsWith('-n'))?.replace('-n', '') || '10';
        const file = args.find(arg => !arg.startsWith('-')) || '';
        return ['-Command', `Get-Content "${file}" | Select-Object -Last ${lines}`];
      }
      return args;
    }
  }
};

export function translateUnixToWindows(command: string): string {
  const translations: Record<string, string> = {
    'ls': 'dir',
    'cat': 'type',
    'cp': 'copy',
    'mv': 'move',
    'rm': 'del',
    'mkdir': 'md',
    'rmdir': 'rd',
    'pwd': 'cd',
    'grep': 'findstr',
    'which': 'where',
    'ps': 'tasklist',
    'kill': 'taskkill /PID'
  };

  let translatedCommand = command;
  for (const [unix, windows] of Object.entries(translations)) {
    const regex = new RegExp(`\\b${unix}\\b`, 'g');
    translatedCommand = translatedCommand.replace(regex, windows);
  }

  return translatedCommand;
}

export function getSupportedUnixCommands(): string[] {
  return Object.keys(commandTranslations);
}