package statemutest.modeling;

import knowledge.modeling.CodeGenerator;
import knowledge.modeling.Finder;
import org.apache.commons.io.FileUtils;
import org.apache.commons.io.filefilter.SuffixFileFilter;
import org.apache.log4j.Logger;

import javax.tools.*;
import java.io.*;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Locale;
import java.util.jar.Attributes;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import java.util.jar.Manifest;

public class JarGenerator {
    // Jar file is deleted when the VM terminates
    // all temporary files too
    // https://docs.oracle.com/javase/7/docs/api/java/io/File.html#deleteOnExit%28%29
    Logger log = Logger.getLogger(JarGenerator.class);

    CodeGenerator codeGenerator = new CodeGenerator();
    Finder finder = new Finder();
    JavaCompiler javaCompiler = ToolProvider.getSystemJavaCompiler();
    File javaDir;
    File classesDir;
    String classpath;
    File jarFile;

    public JarGenerator(String classpath) {
        codeGenerator.setForTesting(true);
        this.classpath = classpath;
    }

    public File generateJarFile(String xmiFilepath) {
        finder.setFilePath(xmiFilepath);
        finder.load();
        codeGenerator.setFinder(finder);
        codeGenerator.generate();
        if (generateJavaCode() && generateCompiledCode() && generateJar()) {
            log.info("Jar generated");
        } else {
            log.error("Something bad happened while generating Jar");
            return null;
        }
        return jarFile;
    }

    private boolean generateJavaCode() {
        try {
            File tempDir = Files.createTempDirectory("statemutest-code-generator-java-").toFile();
            tempDir.deleteOnExit();
            log.debug("tempDir created in " + tempDir.getCanonicalPath());
            for (CodeGenerator.CodePiece codePiece : codeGenerator.getCodePieces()) {
                File javaFile = new File(tempDir, codePiece.getName().replace(".", File.separator) + ".java");
                String content = codePiece.toString();
                if (javaFile.getParentFile().exists() || javaFile.getParentFile().mkdirs()) {
                    FileOutputStream ostream = new FileOutputStream(javaFile);
                    ostream.write(content.getBytes());
                    ostream.close();
                    log.debug("Java file created in " + javaFile.getCanonicalPath());
                } else {
                    log.error("Error while creating code piece path in " + javaFile.getCanonicalPath());
                }
            }
            javaDir = tempDir;
            return true;
        } catch (IOException exception) {
            log.error("Error while handling files in temp dir");
            log.error(exception);
        }
        return false;
    }

    private boolean generateCompiledCode() {
        try {
            classesDir = Files.createTempDirectory("statemutest-code-generator-classes-").toFile();
            classesDir.deleteOnExit();
            ArrayList<File> javaFiles = new ArrayList<File>(FileUtils.listFiles(javaDir, new String[] { "java" }, true));
            DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
            StandardJavaFileManager javaFileManager = javaCompiler.getStandardFileManager(diagnostics, null, null);
            Iterable<? extends JavaFileObject> sources = javaFileManager.getJavaFileObjectsFromFiles(javaFiles);
            JavaCompiler.CompilationTask task = javaCompiler.getTask(null, javaFileManager, diagnostics,
                    Arrays.asList(new String[] { "-cp", classpath, "-d", classesDir.getCanonicalPath() }), null, sources);
            if (task.call()) {
                log.debug("Classes generated in " + classesDir.getCanonicalPath());
                return true;
            } else {
                for (Diagnostic diagnostic : diagnostics.getDiagnostics()) {
                    log.error(diagnostic.getSource() + ", " + diagnostic.getLineNumber() + ", " + diagnostic.getMessage(Locale.ENGLISH));
                }
                return false;
            }
        }
        catch (IOException exception) {
            log.error(exception.getMessage());
            return false;
        }
    }

    private boolean generateJar() {
        Manifest manifest = new Manifest();
        manifest.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");
        try {
            jarFile = Files.createTempFile("statemutest-jar-", ".jar").toFile();
            jarFile.deleteOnExit();
            JarOutputStream jar = new JarOutputStream(new FileOutputStream(jarFile));
            for (File classFile : classesDir.listFiles()) {
                add(classFile, jar);
            }
            jar.close();
            log.debug("Jar file generated in " + jarFile.getCanonicalPath());
            return true;
        } catch (IOException exception) {
            log.error(exception.getMessage());
            return false;
        }
    }

    // from StackOverflow
    // modified because the code was not working at beginning
    private void add(File source, JarOutputStream target) throws IOException
    {
        BufferedInputStream in = null;
        try
        {
            String name = source.getPath().replace("\\", "/");
            String classesDirName = classesDir.getPath().replace("\\", "/");
            // added
            name = name.replace(classesDirName + "/", "");
            if (source.isDirectory())
            {
                if (!name.isEmpty())
                {
                    if (!name.endsWith("/"))
                        name += "/";
                    JarEntry entry = new JarEntry(name);
                    entry.setTime(source.lastModified());
                    target.putNextEntry(entry);
                    target.closeEntry();
                }
                for (File nestedFile: source.listFiles())
                    add(nestedFile, target);
                return;
            }

            JarEntry entry = new JarEntry(name);
            entry.setTime(source.lastModified());
            target.putNextEntry(entry);
            in = new BufferedInputStream(new FileInputStream(source));

            byte[] buffer = new byte[1024];
            while (true)
            {
                int count = in.read(buffer);
                if (count == -1)
                    break;
                target.write(buffer, 0, count);
            }
            target.closeEntry();
        }
        finally
        {
            if (in != null)
                in.close();
        }
    }
}
