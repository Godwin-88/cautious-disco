declare module "bpmn-js" {
  interface BpmnViewerOptions {
    container: HTMLElement;
    width?: string;
    height?: string;
    additionalModules?: any[];
    moddleExtensions?: Record<string, any>;
  }

  interface BpmnViewer {
    importXML(xml: string): Promise<{ warnings: string[] }>;
    destroy(): void;
    saveXML(options: { format: boolean }): Promise<{ xml: string }>;
    saveSVG(): Promise<{ svg: string }>;
    on(event: string, callback: (...args: any[]) => void): void;
    off(event: string, callback?: (...args: any[]) => void): void;
    get(moduleName: string): any;
    attachTo(container: HTMLElement): void;
    detach(): void;
    clear(): void;
  }

  const Viewer: {
    new(options: BpmnViewerOptions): BpmnViewer;
  };
  export default Viewer;
}

declare module "bpmn-js/lib/Modeler" {
  interface BpmnModelerOptions {
    container: HTMLElement;
    width?: string;
    height?: string;
    additionalModules?: any[];
    moddleExtensions?: Record<string, any>;
    keyboard?: { bindTo?: Document };
    propertiesPanel?: { parent?: HTMLElement };
  }

  class Modeler {
    constructor(options: BpmnModelerOptions);
    importXML(xml: string): Promise<{ warnings: string[] }>;
    destroy(): void;
    saveXML(options: { format: boolean }): Promise<{ xml: string }>;
    saveSVG(): Promise<{ svg: string }>;
    on(event: string, callback: (...args: any[]) => void): void;
    off(event: string, callback?: (...args: any[]) => void): void;
    get(moduleName: string): any;
    attachTo(container: HTMLElement): void;
    detach(): void;
    clear(): void;
  }

  export default Modeler;
}

declare module "bpmn-js/lib/viewer" {
  export { default } from "bpmn-js";
}

declare module "bpmn-js-token-simulation" {
  const tokenSimulationModule: any;
  export default tokenSimulationModule;
}

declare module "diagram-js-minimap" {
  const minimapModule: any;
  export default minimapModule;
}

declare module "@bpmn-io/properties-panel" {
  const propertiesPanelModule: any;
  export default propertiesPanelModule;
}

declare module "bpmn-js-color-picker" {
  const colorPickerModule: any;
  export default colorPickerModule;
}