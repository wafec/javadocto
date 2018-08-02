package statemutest.application;

import com.esotericsoftware.yamlbeans.YamlReader;
import org.apache.commons.cli.*;
import org.apache.commons.text.WordUtils;
import org.apache.log4j.Logger;
import statemutest.application.concretization.GenericConcretization;
import statemutest.application.concretization.PythonConcretization;

import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

public class TestCaseConcretization {
    static Logger log = Logger.getLogger(TestCaseConcretization.class);

    String language;
    String testSummaryFilePath;

    TestCaseConcretization(String language, String testSummaryFilePath) {
        this.language = language;
        this.testSummaryFilePath = testSummaryFilePath;
    }

    void generate() {
        GenericConcretization concretization = null;
        String extension = null;
        switch (language) {
            case "python":
                concretization = new PythonConcretization(
                        testSummaryFilePath
                );
                extension = ".py";
                break;
        }
        if (concretization != null) {
            GenericConcretization.TestScript testScript = concretization.generateTestScript();
            writeDownTestScript(testScript, extension);
        } else {
            log.warn("Unknown language selected");
        }
    }

    void writeDownTestScript(GenericConcretization.TestScript testScript, String extension) {
        try {
            FileWriter writer = new FileWriter("test_" + testScript.testScriptFictitiousName.toLowerCase() + extension);
            writer.write(testScript.testScriptBody);
            writer.flush();
            writer.close();
            log.info("Test " + testScript.testScriptFictitiousName + " generated with success");
        } catch (IOException exception) {
            log.error(exception.getMessage());
        }
    }

    public static void main(String[] args) {
        Options options = new Options();

        Option languageOption = new Option("l", "lang", true, "Test script language");
        languageOption.setRequired(true);
        options.addOption(languageOption);

        Option testSummaryOption = new Option("s", "summary", true, "Test summary");
        testSummaryOption.setRequired(true);
        options.addOption(testSummaryOption);

        CommandLineParser parser = new DefaultParser();
        try {
            CommandLine commandLine = parser.parse(options, args);
            new TestCaseConcretization(
                    commandLine.getOptionValue("lang"),
                    commandLine.getOptionValue("summary")
            ).generate();
        } catch (ParseException exception) {
            log.error(exception.getMessage());
        }
    }
}
