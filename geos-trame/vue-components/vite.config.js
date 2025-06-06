export default {
  base: "./",
  build: {
    lib: {
      entry: "./src/main.js",
      name: "geos_trame",
      formats: ["umd"],
      fileName: "geos_trame",
    },
    rollupOptions: {
      external: ["vue"],
      output: {
        globals: {
          vue: "Vue",
        },
      },
    },
    outDir: "../src/geos/trame/module/serve",
    assetsDir: ".",
  },
};
