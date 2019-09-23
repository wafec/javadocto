package statemutest.util;

import com.esotericsoftware.yamlbeans.YamlReader;
import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.StringUtils;
import statemutest.modeling.JarGenerator;
import xstate.core.InputReceiver;
import xstate.support.Input;

import java.io.File;
import java.lang.reflect.Field;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;

public class InstanceProvider {
    private String _xmiFilepath;
    private String _instantiationFilepath;
    private String _classpath;
    private URLClassLoader _urlClassloader;

    public InstanceProvider(String xmiFilepath, String instantiationFilepath, String classpath) {
        this._xmiFilepath = xmiFilepath;
        this._instantiationFilepath = instantiationFilepath;
        this._classpath = classpath;
        this.initializeComponent();
    }

    private void initializeComponent() {
        try {
            File jarFile = new JarGenerator(this._classpath).generateJarFile(this._xmiFilepath);
            this._urlClassloader = new URLClassLoader(new URL[]{jarFile.toURI().toURL()});
        } catch(Exception exc) {

        }
    }

    public RawInput getRawInput(String qualifiedName) {
        try {
            Class clazz = _urlClassloader.loadClass(qualifiedName);
            if (clazz != null) {
                return new RawInput(clazz.newInstance(), _urlClassloader, clazz);
            }
        } catch (Exception exc) {

        }
        return null;
    }

    public InputReceiver getReceiver(String qualifiedName) {
        try {
            InputReceiver receiver = null;
            if (!StringUtils.isEmpty(this._instantiationFilepath)) {
                YamlReader yamlReader = new YamlReader(FileUtils.readFileToString(new File(this._instantiationFilepath)));
                receiver = (InputReceiver) yamlReader.read(_urlClassloader.loadClass(qualifiedName));
            } else {
                receiver = (InputReceiver) _urlClassloader.loadClass(qualifiedName).newInstance();
            }
            return receiver;
        } catch (Exception exc) {
            exc.printStackTrace();
        }
        return null;
    }

    public static class RawInput {
        private Object _rawObject;
        private URLClassLoader _urlClassloader;
        private Class _clazz;

        private RawInput(Object rawObject, URLClassLoader _urlClassloader, Class clazz) {
            this._rawObject = rawObject;
            this._urlClassloader = _urlClassloader;
            this._clazz = clazz;
        }

        public Input get() {
            try {
                return Input.createTo(this._rawObject, _clazz);
            } catch (Exception exc) {

            }
            return null;
        }

        public void setValue(String fieldName, Object value) {
            try {
                _rawObject.getClass().getDeclaredField(fieldName).set(_rawObject, value);
            } catch (Exception exc) {

            }
        }
    }
}
