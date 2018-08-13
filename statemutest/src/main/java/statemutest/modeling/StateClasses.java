package statemutest.modeling;

import com.esotericsoftware.yamlbeans.YamlException;
import com.esotericsoftware.yamlbeans.YamlReader;
import org.apache.log4j.Logger;
import statemutest.application.GenericSetup;
import xstate.core.InputReceiver;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.lang.reflect.Field;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.ArrayList;
import java.util.Map;
import java.util.Optional;

// TO-DO: using this code in other classes like as TestCaseGenerator
public class StateClasses {
    static Logger log = Logger.getLogger(StateClasses.class);

    File jarFile;
    String testClass;
    File instanceSpecification;
    ArrayList<String> inputs;
    ArrayList<String> stateIdentities;

    URLClassLoader urlClassLoader;
    Class loadedTestClass;
    ArrayList<Class> loadedInputs;
    String instanceSpecificationText;
    boolean loaded = false;

    public StateClasses(File jarFile, String testClass, File instanceSpecification, ArrayList<String> inputs, ArrayList<String> stateIdentities) {
        this.jarFile = jarFile;
        this.testClass = testClass;
        this.instanceSpecification = instanceSpecification;
        this.inputs = inputs;
        this.stateIdentities = stateIdentities;

        loadClasses();
        loadSpecification();

        loaded = true;
    }

    public StateClasses(GenericSetup genericSetup) {
        this(
            new JarGenerator(genericSetup.classpath).generateJarFile(genericSetup.xmiFilePath),
            genericSetup.testClassQualifiedName,
            new File(genericSetup.instanceSpecFilePath),
            new ArrayList<>(genericSetup.inputQualifiedNames),
            new ArrayList<>(genericSetup.stateIdentities)
        );
    }

    final void loadClasses() {
        try {
            urlClassLoader = URLClassLoader.newInstance(new URL[] { jarFile.toURI().toURL() });
            loadedTestClass = urlClassLoader.loadClass(testClass);
            loadedInputs = new ArrayList<>();
            for (String input : inputs) {
                loadedInputs.add(urlClassLoader.loadClass(input));
            }
            log.debug("States machine class and input classes loaded");
        } catch (IOException exception) {
            log.error(exception.getMessage());
        } catch (ClassNotFoundException exception) {
            log.error(exception.getMessage());
        }
    }

    final void loadSpecification() {
        try {
            FileInputStream fileStream = new FileInputStream(this.instanceSpecification);
            byte[] content = new byte[fileStream.available()];
            fileStream.read(content);
            fileStream.close();
            this.instanceSpecificationText = new String(content);
            log.debug("Specification loaded in memory");
        } catch (IOException exception) {
            log.error(exception.getMessage());
        }
    }

    public InputReceiver createTestClassInstance() {
        try {
            YamlReader reader = new YamlReader(instanceSpecificationText);
            Object testClassInstance = reader.read(loadedTestClass);
            return (InputReceiver) (testClassInstance == null ? loadedTestClass.newInstance() : testClassInstance);
        } catch (YamlException exception) {
            log.error(exception.getMessage());
        } catch (IllegalAccessException | InstantiationException exception) {
            log.error(exception.getMessage());
        }

        try {
            return (InputReceiver) loadedTestClass.newInstance();
        } catch (IllegalAccessException | InstantiationException exception) {
            log.error(exception.getMessage());
        }

        return null;
    }

    public <T> T createInputInstanceFromMap(Map<String, String> map, Class<T> clazz) {
        try {
            T instance = clazz.newInstance();
            for (String key : map.keySet()) {
                String strValue = map.get(key);
                Field field = clazz.getField(key);
                // working with integers
                field.set(instance, Integer.valueOf(strValue));
            }
            return instance;
        } catch (IllegalAccessException | InstantiationException exception) {
            log.error(exception);
        } catch (NoSuchFieldException exception) {
            log.error(exception);
        }
        return null;
    }

    public Class getInputClassByQualifiedName(String qualifiedName) {
        Optional<Class> opt = loadedInputs.stream().filter(i -> i.getCanonicalName().equals(qualifiedName))
                .findFirst();
        if (opt.isPresent()) {
            return opt.get();
        } else {
            return null;
        }
    }
}
