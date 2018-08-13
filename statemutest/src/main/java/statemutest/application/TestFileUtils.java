package statemutest.application;

import com.esotericsoftware.yamlbeans.YamlReader;
import com.esotericsoftware.yamlbeans.YamlWriter;
import com.github.javafaker.Faker;
import org.apache.commons.cli.*;
import org.apache.log4j.Logger;
import statemutest.testcase.GenericGeoTestCaseGenerator;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

public class TestFileUtils {
    static Logger log = Logger.getLogger(TestFileUtils.class);

    TestFileUtils() {

    }

    static abstract class BaseRunner {
        public abstract void processFunction();

        YamlReader getSetupReader(String filePath) throws IOException {
            YamlReader reader = new YamlReader(new FileReader(filePath));
            reader.getConfig().setClassTag("setup", TestSetup.class);
            reader.getConfig().setClassTag("conf", GenericSetup.class);
            reader.getConfig().setClassTag("stateInputMapping", GenericGeoTestCaseGenerator.UserDefinedStateInputMapping.class);
            reader.getConfig().setClassTag("mgeovsl", TestCaseGeneration.MgeoVslSetup.class);
            reader.getConfig().setClassTag("meter", TestMeter.MeterSetup.class);
            return reader;
        }
    }

    public static class SetupOverlayBuilder extends BaseRunner {
        String[] setupFilePaths;

        public SetupOverlayBuilder(String[] setupFilePaths) {
            this.setupFilePaths = setupFilePaths;
            this.normalizeSetupFilePaths();
        }

        final void normalizeSetupFilePaths() {
            ArrayList<String> normalized = new ArrayList<>();
            for (String filePath : setupFilePaths) {
                try {
                    File currentFile = new File(filePath);
                    if (currentFile.isDirectory()) {
                        // one level only
                        for (File child : currentFile.listFiles()) {
                            if (child.getCanonicalPath().endsWith(".yaml") && child.exists()) {
                                normalized.add(child.getCanonicalPath());
                            } else {
                                log.debug("The file " + child.getPath() + " has been ignored");
                            }
                        }
                    } else {
                        if (currentFile.getCanonicalPath().endsWith(".yaml") && currentFile.exists())
                            normalized.add(currentFile.getCanonicalPath());
                        else {
                            log.debug("The file " + currentFile.getPath() + " has been ignored");
                        }
                    }
                } catch (IOException exception) {
                    log.error(exception);
                }
            }
            this.setupFilePaths = normalized.toArray(new String[normalized.size()]);
        }

        @Override
        public void processFunction() {
            TestSetup finalSetup = null;
            for (int i = 0; i < setupFilePaths.length; i++) {
                String setupFilePath = setupFilePaths[i];
                try {
                    TestSetup base = getSetupReader(setupFilePath).read(TestSetup.class);
                    if (i == 0)
                        finalSetup = base.clone();
                    else {
                        finalSetup = base.overlap(finalSetup);
                    }
                } catch (IOException exception) {
                    log.warn("File " + setupFilePath + " could not be read");
                }
            }
            if (finalSetup == null) {
                log.warn("None file processed");
                return;
            }
            Faker faker = new Faker();
            try {
                String finalFilePath = "test-setup-" + faker.name().firstName() + ".yaml";
                YamlWriter writer = new YamlWriter(new FileWriter(finalFilePath));
                writer.getConfig().setClassTag("setup", TestSetup.class);
                writer.getConfig().setClassTag("conf", GenericSetup.class);
                writer.getConfig().setClassTag("stateInputMapping", GenericGeoTestCaseGenerator.UserDefinedStateInputMapping.class);
                writer.getConfig().setClassTag("mgeovsl", TestCaseGeneration.MgeoVslSetup.class);
                writer.getConfig().setClassTag("meter", TestMeter.MeterSetup.class);
                writer.write(finalSetup);
                writer.close();
                log.info("Overlapped file generated as " + finalFilePath);
            } catch (IOException exception) {
                log.error(exception);
            }
        }
    }

    public static void main(String[] args) {
        Options options = new Options();

        Option functionOption = new Option("f", "function", true, "Function name");
        functionOption.setRequired(true);
        options.addOption(functionOption);

        Option parametersOption = new Option("p", "parameters", true, "Parameter list");
        parametersOption.setArgs(Option.UNLIMITED_VALUES);
        options.addOption(parametersOption);

        CommandLineParser parser = new DefaultParser();
        try {
            CommandLine commandLine = parser.parse(options, args);
            BaseRunner runner = null;
            switch (commandLine.getOptionValue("function")) {
                case "overlay":
                    if (commandLine.hasOption("parameters")) {
                        runner = new SetupOverlayBuilder(commandLine.getOptionValues("parameters"));
                    }
                    break;
            }
            if (runner != null) {
                runner.processFunction();
            } else {
                log.error("Something bad happened, it is likely a missing thing on the command provided");
            }
        } catch (ParseException exception) {
            log.error(exception);
        }
    }
}
