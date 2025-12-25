declare module "*.yaml" {
  const content: Record<string, { title: string; tag: string[] }[]>;
  export default content;
}
