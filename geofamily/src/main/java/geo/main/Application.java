package geo.main;

import geo.algorithm.BinaryInteger;
import geo.algorithm.Geo;
import geo.problem.Booth;

public class Application {
    public static void main(String[] args) {
        System.out.println("Hello World!");
        Geo geo = new Geo(
                3.0,
                50000,
                new Booth.ObjectiveOne(),
                Booth.searchDomain);
        geo.run();
        System.out.println("The End!");
    }
}